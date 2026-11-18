# Lab 10 – Jenkins CI/CD Pipeline for a Python Project

**Student:** Hayam Itani
**Jenkinsfile:** [`Jenkinsfile_Hayam_Itani`](Jenkinsfile_Hayam_Itani)
**Jenkins job:** `Python-CI-CD` (Pipeline script from SCM)

## Project structure

| File | Purpose |
|------|---------|
| `app.py` | Application: `greet(name)` returns `Hello, <name> from Hayam Itani!` |
| `tests/test_app.py` | Unit test for `greet` |
| `tests/test_deploy.py` | Unit tests for the deployment script |
| `deploy.py` | Local deployment script used by the Deploy stage (Part 4) |
| `requirements.txt` | Pinned tools: flake8, pytest, coverage, bandit |
| `pytest.ini` | Points pytest at `tests/` and puts the project root on the import path |
| `.coveragerc` | Coverage settings: measure project code, skip `venv/` and `tests/` |
| `Jenkinsfile_Hayam_Itani` | Declarative pipeline |

## Pipeline stages

| Stage | What it does | Fails the build when |
|-------|--------------|----------------------|
| Setup | Creates `venv` and installs `requirements.txt` | A dependency fails to install |
| Lint | `flake8 app.py deploy.py tests` | Any style error |
| Test | `pytest -v` | Any test fails |
| **Coverage** (Part 4) | `coverage run -m pytest`, then HTML, XML and console reports; HTML report and `coverage.xml` are archived as build artefacts | Total coverage is below 80% |
| **Security Scan** (Part 4) | `bandit -r . -x ./venv,./tests` | Bandit reports any issue |
| **Deploy** (Part 4) | Runs `deploy.py` | The copy or the smoke test fails |

The workspace is wiped after every build (`cleanWs()`), so each build starts from a clean checkout.

## Changes made for Part 4

1. **Coverage stage.** Added `coverage` to the requirements and a `Coverage` stage that runs the test suite under coverage.py, prints a report with missing lines, and writes `htmlcov/` and `coverage.xml`. These are archived on the build page, even if the stage fails. A `--fail-under=80` gate stops the pipeline if coverage drops.
2. **Security Scan stage.** Added `bandit` and a `Security Scan` stage that scans the project's Python code (excluding the virtual environment and tests). Bandit exits with a non-zero code when it finds an issue, which fails the build. I checked this by temporarily adding a file using `subprocess.call(..., shell=True)`: Bandit reported B602/B607/B404 and exited with code 1.
3. **Deployment.** Replaced the `echo` placeholder with `deploy.py`, a simple local deployment that:
   - copies `app.py` and `requirements.txt` to `<DEPLOY_DIR>/current`, outside the Jenkins workspace (default `~/deployments/python-ci-cd`, can be changed with the `DEPLOY_DIR` environment variable);
   - writes `BUILD_INFO.txt` with the Jenkins build number, Git commit and UTC timestamp;
   - smoke-tests the deployed copy by importing it and checking `greet("World")`;
   - refuses unsafe targets: a filesystem root, a folder inside the workspace, or a `current` folder that this script did not create.

   `deploy.py` has its own unit tests, so it is also linted, covered and scanned by the earlier stages.

## Other changes to the lab template

- **Runs on Windows and Linux.** The template uses `sh` and `source venv/bin/activate`, which fail on a Windows Jenkins because Windows virtual environments use `venv\Scripts\`. A small `venvPython()` helper calls the virtual environment's Python directly, using `sh` on Unix agents and `bat` on Windows agents.
- **`pytest` added to `requirements.txt`.** The Test stage runs pytest, but the template only listed flake8.
- **`app.py` greeting updated** to `Hello, {name} from Hayam Itani!` so it matches the required test.
- **Tool versions pinned** so every build installs the same versions.

## Jenkins job configuration

- New Item → Pipeline → name `Python-CI-CD`
- Pipeline → Definition: *Pipeline script from SCM* → SCM: *Git*
- Repository URL: this repository
- Branch Specifier: `*/main`
- **Script Path: `Jenkinsfile_Hayam_Itani`** (the default `Jenkinsfile` would not be found)

## Jenkins build output

> **TODO (Hayam): replace this section with the real output after running the build.**
> Add screenshots to a `screenshots/` folder (Stage View showing all stages green, and the console output) and link them here, or paste the end of the console log below.

```text
<paste the Jenkins console output here>
```
