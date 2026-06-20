# Kiwoom CLI Restructure & Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 소스 코드를 `src/kiwoom` 패키지 하위로 이동하여 패키지화하고, `setup.py`를 생성하여 `kiwoom` 커맨드로 실행할 수 있도록 패키징 설정을 수행하며, 사용 설명서(`USER_GUIDE.md`)를 `README.md`에 병합 및 원본은 삭제합니다.

**Architecture:**
- **패키지 구조**: `src/kiwoom/` 하위에 `__init__.py`, `config.py`, `client.py`, `cli.py`를 위치시킵니다.
- **임포트 경로 변경**: 모듈들의 패키지화에 따라 `cli.py` 및 테스트 코드들의 임포트 경로를 `kiwoom` 패키지 기반으로 업데이트합니다.
- **패키징 배포**: `setup.py` 내의 `console_scripts`를 설정하여 `kiwoom` 단독 명령어로 `kiwoom.cli:main`을 실행할 수 있게 연결합니다.
- **문서화**: 기존 `docs/USER_GUIDE.md`를 `README.md`로 완전 병합하고 깔끔히 통합 관리합니다.

**Tech Stack:**
- Python 3
- `setuptools` (패키징 및 설치)
- `click`, `requests` (기존 의존성)
- `pytest`, `requests-mock` (기존 테스트 의존성)

## Global Constraints
- 모든 기능은 이전에 구현한 로직을 그대로 보존하고, 테스트가 100% 통과해야 합니다.
- 패키지 모듈 경로는 `kiwoom` 패키지(예: `from kiwoom.config import ...`)를 사용합니다.
- 사용자는 `pip install -e .` 명령어를 통해 개발 모드로 로컬에 바로 설치하여 `kiwoom` 명령어를 사용할 수 있어야 합니다.

---

### Task 1: Package Restructuring & Import Updates

**Files:**
- Create: `src/kiwoom/__init__.py`
- Move: `config.py` ➜ `src/kiwoom/config.py`
- Move: `client.py` ➜ `src/kiwoom/client.py`
- Move: `cli.py` ➜ `src/kiwoom/cli.py`
- Modify: `src/kiwoom/cli.py`
- Modify: `tests/test_config.py`
- Modify: `tests/test_client.py`
- Modify: `tests/test_client_queries.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Produces: `kiwoom` 파이썬 패키지 구조 및 업데이트된 내부 모듈 임포트

- [ ] **Step 1: Create directories and move files**

Run:
```bash
mkdir -p src/kiwoom
touch src/kiwoom/__init__.py
mv config.py src/kiwoom/config.py
mv client.py src/kiwoom/client.py
mv cli.py src/kiwoom/cli.py
```

- [ ] **Step 2: Run test to verify it fails (Imports broken)**

Run: `PYTHONPATH=src pytest`
Expected: FAIL due to `ModuleNotFoundError` on test config/client/cli imports.

- [ ] **Step 3: Modify imports in implementation and test files**

Modify: `src/kiwoom/cli.py` (line 3-4)
```python
# Before
from config import ConfigManager
from client import KiwoomClient

# After
from kiwoom.config import ConfigManager
from kiwoom.client import KiwoomClient
```

Modify: `tests/test_config.py` (line 5)
```python
# Before
from config import ConfigManager

# After
from kiwoom.config import ConfigManager
```

Modify: `tests/test_client.py` (line 4-5)
```python
# Before
from config import ConfigManager
from client import KiwoomClient

# After
from kiwoom.config import ConfigManager
from kiwoom.client import KiwoomClient
```

Modify: `tests/test_client_queries.py` (line 3)
```python
# Before
from client import KiwoomClient

# After
from kiwoom.client import KiwoomClient
```

Modify: `tests/test_cli.py` (line 6)
```python
# Before
from cli import main

# After
from kiwoom.cli import main
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src pytest`
Expected: PASS (10 passed)

- [ ] **Step 5: Commit changes**

```bash
git add src/ tests/
git commit -m "refactor: restructure files into src/kiwoom package and update import paths"
```

---

### Task 2: setup.py Integration & Executable Command Verification

**Files:**
- Create: `setup.py`

**Interfaces:**
- Produces: `setup.py` 설치 사양
- CLI 명령어: `kiwoom` (엔트리 포인트: `kiwoom.cli:main`)

- [ ] **Step 1: Write setup.py configuration**

Create: `setup.py`
```python
from setuptools import setup, find_packages

setup(
    name="kiwoom-cli",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "requests",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "kiwoom=kiwoom.cli:main",
        ],
    },
)
```

- [ ] **Step 2: Install package in editable mode**

Run: `pip install -e .`
Expected: Successfully installed `kiwoom-cli` and links command `kiwoom`.

- [ ] **Step 3: Verify the executable command works**

Run: `kiwoom --help`
Expected: click 도움말이 터미널에 정상 출력되어야 함.

- [ ] **Step 4: Run tests without PYTHONPATH override**

Run: `pytest`
Expected: PASS (site-packages / editable link가 걸려 있어 PYTHONPATH를 주지 않아도 import가 성공해야 함)

- [ ] **Step 5: Commit setup.py**

```bash
git add setup.py
git commit -m "feat: add setup.py and configure console entrypoint for kiwoom command"
```

---

### Task 3: Documentation Merging and Cleanup

**Files:**
- Modify: `README.md`
- Delete: `docs/USER_GUIDE.md`

- [ ] **Step 1: Merge USER_GUIDE.md contents into README.md**

`docs/USER_GUIDE.md` 내용을 온전히 복사하여 `README.md` 하단에 결합합니다. 기존 README에 있는 기본 내용과 자연스럽게 병합합니다.

- [ ] **Step 2: Delete USER_GUIDE.md**

Run: `git rm docs/USER_GUIDE.md` (or file delete)

- [ ] **Step 3: Commit documentation updates**

```bash
git add README.md
git commit -m "docs: merge USER_GUIDE.md into README.md and cleanup docs folder"
```
