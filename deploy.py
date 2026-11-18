"""Simple local deployment for jenkins_project.

Copies the application into a deployment directory outside the Jenkins
workspace, records build metadata, then smoke-tests the deployed copy.

The target directory is read from the DEPLOY_DIR environment variable and
defaults to ~/deployments/python-ci-cd. The release is written to
<DEPLOY_DIR>/current and replaced on every deployment.
"""
import importlib.util
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
FILES_TO_DEPLOY = ("app.py", "requirements.txt")
BUILD_INFO_FILE = "BUILD_INFO.txt"
EXPECTED_GREETING = "Hello, World from Hayam Itani!"
DEFAULT_DEPLOY_DIR = Path.home() / "deployments" / "python-ci-cd"


def get_deploy_dir():
    """Return the validated deployment directory."""
    raw = os.environ.get("DEPLOY_DIR", "").strip()
    target = (Path(raw).expanduser() if raw else DEFAULT_DEPLOY_DIR).resolve()

    if target == Path(target.anchor):
        raise ValueError("DEPLOY_DIR must not be a filesystem root.")
    if target == PROJECT_ROOT or PROJECT_ROOT in target.parents:
        raise ValueError(
            "DEPLOY_DIR must be outside the project/workspace, "
            "because the workspace is wiped after every build."
        )
    return target


def deploy(target, build_number, commit):
    """Copy the application into <target>/current and return that path."""
    release_dir = target / "current"

    if release_dir.exists():
        # Only replace a folder that a previous run of this script created.
        if not (release_dir / BUILD_INFO_FILE).is_file():
            raise RuntimeError(
                f"Refusing to overwrite {release_dir}: "
                f"it was not created by this deploy script."
            )
        shutil.rmtree(release_dir)

    release_dir.mkdir(parents=True)
    for name in FILES_TO_DEPLOY:
        shutil.copy2(PROJECT_ROOT / name, release_dir / name)

    deployed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (release_dir / BUILD_INFO_FILE).write_text(
        f"build_number={build_number}\n"
        f"git_commit={commit}\n"
        f"deployed_at_utc={deployed_at}\n",
        encoding="utf-8",
    )
    return release_dir


def smoke_test(release_dir):
    """Import the deployed app.py and check that it responds correctly."""
    spec = importlib.util.spec_from_file_location(
        "deployed_app", release_dir / "app.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.greet("World")
    if result != EXPECTED_GREETING:
        raise RuntimeError(
            f"Smoke test failed: expected {EXPECTED_GREETING!r}, "
            f"got {result!r}"
        )
    return result


def main():
    build_number = os.environ.get("BUILD_NUMBER", "local")
    commit = os.environ.get("GIT_COMMIT", "unknown")

    try:
        target = get_deploy_dir()
        release_dir = deploy(target, build_number, commit)
        greeting = smoke_test(release_dir)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"Deployment failed: {exc}", file=sys.stderr)
        return 1

    print(f"Deployed build {build_number} ({commit[:7]}) to {release_dir}")
    print(f"Smoke test passed: {greeting}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
