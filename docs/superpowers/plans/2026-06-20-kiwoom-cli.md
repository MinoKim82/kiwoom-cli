# Kiwoom CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kiwoom REST API를 사용하여 다중 사용자(3명)의 자격 증명(config)과 세션 토큰(tokens)을 안전하게 분리 관리하고, 토큰 만료 10분 전에 자동으로 갱신하면서 계좌 번호 및 평가 잔고/보유 종목을 상세 조회하는 CLI 프로그램을 작성합니다.

**Architecture:**
- `ConfigManager` (`config.py`): 사용자 홈 디렉토리(`~/.kiwoom/`) 내에 `config.json`(자격 증명) 및 `tokens.json`(동적 세션 토큰)을 읽고 쓰는 책임을 캡슐화합니다.
- `KiwoomClient` (`client.py`): REST API 요청을 담당하며, 요청 전 캐시된 토큰의 KST 기준 만료 임박(10분 미만) 여부를 판단하여 자동으로 토큰을 발급(`au10001`)하고 캐시 파일에 보관합니다. 연속 조회(`cont-yn: "Y"`) 루프 처리를 포함합니다.
- CLI Entrypoint (`cli.py`): `click` 라이브러리를 이용하여 `--user` 옵션에 따라 유저별 컨텍스트를 분리하고, `accounts` 및 `balance` 명령어를 실행하여 터미널에 가독성이 높은 표 형태로 출력합니다.

**Tech Stack:**
- Python 3
- `requests` (API 통신용)
- `click` (CLI 프레임워크)
- `pytest` (테스트용)
- `requests-mock` (API 모킹 테스트용)

## Global Constraints
- 모든 코드는 PEP 8 파이썬 코딩 스타일을 준수합니다.
- 사용자 정보 보안을 위해, `config.json`은 절대 수정(Write)하지 않고 읽기 전용으로 사용하며, `tokens.json` 파일만 갱신 시 업데이트합니다.
- 에러 발생 시 키움 REST API의 `return_code`와 `return_msg`를 명확히 출력하여 오류를 식별할 수 있어야 합니다.

---

### Task 1: Project Scaffolding & Configuration Manager (`config.py`)

**Files:**
- Create: `config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `ConfigManager` 클래스 및 메서드
  - `ConfigManager(base_dir=None)`: 기본 경로는 `~/.kiwoom` 이며, 테스트 시 임의 경로 지정 가능
  - `load_credentials(user_id) -> dict`: `appkey`, `secretkey` 반환
  - `load_token(user_id) -> dict`: `token`, `expires_dt` 반환
  - `save_token(user_id, token, expires_dt) -> None`: `tokens.json` 파일에 저장

- [ ] **Step 1: Write the failing test**

Create: `tests/test_config.py`
```python
import os
import json
import tempfile
import pytest
from config import ConfigManager

def test_config_manager_load_and_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Given: config.json 사전 생성
        config_data = {
            "users": {
                "user1": {
                    "appkey": "key123",
                    "secretkey": "sec123"
                }
            }
        }
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
            
        cm = ConfigManager(base_dir=tmpdir)
        
        # When & Then: 자격 증명 로드 테스트
        creds = cm.load_credentials("user1")
        assert creds == {"appkey": "key123", "secretkey": "sec123"}
        
        # When & Then: 존재하지 않는 유저 예외 처리
        with pytest.raises(KeyError):
            cm.load_credentials("non_exist")
            
        # When & Then: 토큰 저장 및 로드 테스트
        cm.save_token("user1", "token_val", "20260620120000")
        token_info = cm.load_token("user1")
        assert token_info == {"token": "token_val", "expires_dt": "20260620120000"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'config'"

- [ ] **Step 3: Write minimal implementation**

Create: `config.py`
```python
import os
import json

class ConfigManager:
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = os.path.expanduser("~/.kiwoom")
        else:
            self.base_dir = base_dir
            
        os.makedirs(self.base_dir, exist_ok=True)
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.tokens_path = os.path.join(self.base_dir, "tokens.json")

    def load_credentials(self, user_id):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        users = data.get("users", {})
        if user_id not in users:
            raise KeyError(f"User {user_id} not found in configuration.")
        return users[user_id]

    def load_token(self, user_id):
        if not os.path.exists(self.tokens_path):
            return {}
        with open(self.tokens_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(user_id, {})

    def save_token(self, user_id, token, expires_dt):
        data = {}
        if os.path.exists(self.tokens_path):
            with open(self.tokens_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        data[user_id] = {
            "token": token,
            "expires_dt": expires_dt
        }
        with open(self.tokens_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: add ConfigManager for credentials and token caching"
```

---

### Task 2: Kiwoom API Client & Auto-refresh Token Module (`client.py`)

**Files:**
- Create: `client.py`
- Test: `tests/test_client.py`

**Interfaces:**
- Consumes: `ConfigManager`
- Produces: `KiwoomClient` 클래스 및 메서드
  - `KiwoomClient(user_id, config_manager, host="https://api.kiwoom.com")`
  - `get_valid_token() -> str`: 유효한 토큰 반환 (만료 10분 전 자동 갱신 수행)
  - `request_api(endpoint, method="POST", data=None, api_id=None, cont_yn="N", next_key="") -> dict`: 자동 갱신된 토큰을 헤더에 실어 API 호출

- [ ] **Step 1: Write the failing test**

Create: `tests/test_client.py`
```python
import pytest
import requests_mock
from datetime import datetime, timedelta
from config import ConfigManager
from client import KiwoomClient

def test_token_auto_refresh_needed(requests_mock):
    # Given: 만료된 토큰 설정 및 ConfigManager 모킹
    class MockConfigManager:
        def __init__(self):
            self.saved = False
        def load_credentials(self, user_id):
            return {"appkey": "my_appkey", "secretkey": "my_secretkey"}
        def load_token(self, user_id):
            # 15분 전에 만료된 토큰 시뮬레이션
            expired_time = (datetime.now() - timedelta(minutes=15)).strftime("%Y%m%d%H%M%S")
            return {"token": "expired_token", "expires_dt": expired_time}
        def save_token(self, user_id, token, expires_dt):
            self.saved = True
            self.token = token
            self.expires_dt = expires_dt

    mcm = MockConfigManager()
    client = KiwoomClient(user_id="user1", config_manager=mcm, host="https://mockapi.kiwoom.com")

    # oauth2/token API 모킹
    new_expires_dt = (datetime.now() + timedelta(hours=24)).strftime("%Y%m%d%H%M%S")
    requests_mock.post("https://mockapi.kiwoom.com/oauth2/token", json={
        "token": "new_fresh_token",
        "expires_dt": new_expires_dt,
        "return_code": 0
    })

    # When: 토큰 획득 시도
    token = client.get_valid_token()

    # Then: 신규 발급 API가 호출되고 새로운 토큰이 저장되었는지 확인
    assert token == "new_fresh_token"
    assert mcm.saved is True
    assert mcm.token == "new_fresh_token"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_client.py -v`
Expected: FAIL with "ImportError: cannot import name 'KiwoomClient' from 'client'"

- [ ] **Step 3: Write minimal implementation**

Create: `client.py`
```python
import requests
from datetime import datetime, timedelta

class KiwoomClient:
    def __init__(self, user_id, config_manager, host="https://api.kiwoom.com"):
        self.user_id = user_id
        self.config_manager = config_manager
        self.host = host

    def get_valid_token(self):
        token_info = self.config_manager.load_token(self.user_id)
        token = token_info.get("token")
        expires_dt_str = token_info.get("expires_dt")

        refresh_needed = True
        if token and expires_dt_str:
            try:
                # KST 시간으로 저장된 expires_dt 파싱
                expires_at = datetime.strptime(expires_dt_str, "%Y%m%d%H%M%S")
                # 현재 로컬 시간 기준 만료까지 10분 이상 남았는지 체크
                if expires_at - datetime.now() > timedelta(minutes=10):
                    refresh_needed = False
                    return token
            except ValueError:
                pass

        if refresh_needed:
            creds = self.config_manager.load_credentials(self.user_id)
            token_url = f"{self.host}/oauth2/token"
            headers = {"Content-Type": "application/json;charset=UTF-8"}
            body = {
                "grant_type": "client_credentials",
                "appkey": creds["appkey"],
                "secretkey": creds["secretkey"]
            }
            res = requests.post(token_url, headers=headers, json=body)
            res.raise_for_status()
            res_json = res.json()
            
            if res_json.get("return_code", 0) != 0:
                raise Exception(f"Failed to issue token: {res_json.get('return_msg')}")
                
            new_token = res_json["token"]
            new_expires = res_json["expires_dt"]
            self.config_manager.save_token(self.user_id, new_token, new_expires)
            return new_token

    def request_api(self, endpoint, method="POST", data=None, api_id=None, cont_yn="N", next_key=""):
        token = self.get_valid_token()
        url = f"{self.host}{endpoint}"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {token}",
            "cont-yn": cont_yn,
            "next-key": next_key
        }
        if api_id:
            headers["api-id"] = api_id

        if method == "POST":
            res = requests.post(url, headers=headers, json=data or {})
        else:
            res = requests.get(url, headers=headers, params=data)
        
        res.raise_for_status()
        return res.json(), res.headers
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add client.py tests/test_client.py
git commit -m "feat: implement KiwoomClient with auto token refresh logic"
```

---

### Task 3: Accounts and Portfolio Balance Enquiry with Pagination

**Files:**
- Modify: `client.py`
- Test: `tests/test_client_queries.py`

**Interfaces:**
- Consumes: `KiwoomClient`
- Produces: `KiwoomClient` 추가 메서드
  - `get_accounts() -> list`: 유저의 계좌 번호 리스트 반환 (`acctNo` 값 추출)
  - `get_balance(acct_no) -> dict`: 계좌 기본 정보 및 보유 종목 리스트(`stk_cntr_remn`) 수집. `cont-yn == "Y"`인 동안 반복 조회(Pagination)를 수행하여 하나의 리스트로 통합 반환.

- [ ] **Step 1: Write the failing test**

Create: `tests/test_client_queries.py`
```python
import pytest
import requests_mock
from client import KiwoomClient

class MockConfigManager:
    def load_credentials(self, user_id):
        return {"appkey": "key", "secretkey": "sec"}
    def load_token(self, user_id):
        return {"token": "valid_token", "expires_dt": "20360101000000"} # 충분히 먼 미래

def test_get_balance_pagination(requests_mock):
    cm = MockConfigManager()
    client = KiwoomClient(user_id="user1", config_manager=cm, host="https://mockapi.kiwoom.com")

    # 첫 번째 페이지 모킹 (cont-yn: Y, next-key: page2_key)
    requests_mock.post(
        "https://mockapi.kiwoom.com/api/dostk/acnt",
        [
            {
                "json": {
                    "tot_pur_amt": "10000",
                    "stk_cntr_remn": [{"stk_cd": "A005930", "stk_nm": "삼성전자"}]
                },
                "headers": {"cont-yn": "Y", "next-key": "page2_key"},
                "status_code": 200
            },
            {
                "json": {
                    "tot_pur_amt": "10000",
                    "stk_cntr_remn": [{"stk_cd": "A000660", "stk_nm": "SK하이닉스"}]
                },
                "headers": {"cont-yn": "N", "next-key": ""},
                "status_code": 200
            }
        ]
    )

    balance = client.get_balance("1234567890")
    # 검증: 두 페이지의 종목이 정상적으로 통합되었는지 확인
    assert len(balance["stk_cntr_remn"]) == 2
    assert balance["stk_cntr_remn"][0]["stk_nm"] == "삼성전자"
    assert balance["stk_cntr_remn"][1]["stk_nm"] == "SK하이닉스"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_client_queries.py -v`
Expected: FAIL with "AttributeError: 'KiwoomClient' object has no attribute 'get_balance'"

- [ ] **Step 3: Write minimal implementation**

Modify: `client.py`
Add the following methods to `KiwoomClient` class:
```python
    def get_accounts(self):
        res_data, _ = self.request_api(
            endpoint="/api/dostk/acnt",
            method="POST",
            data={},
            api_id="ka00001"
        )
        if res_data.get("return_code", 0) != 0:
            raise Exception(f"API Error: {res_data.get('return_msg')}")
        # 응답 구조 예시: {"acctNo": "1234567890"} 또는 리스트 형태
        # 보통 단일 계좌번호면 문자열, 여러개일 수 있으므로 유연하게 처리
        acct = res_data.get("acctNo")
        if acct:
            return [acct]
        return []

    def get_balance(self, acct_no):
        all_holdings = []
        cont_yn = "N"
        next_key = ""
        summary_data = {}

        while True:
            body = {
                "qry_tp": "2",          # 개별 조회
                "dmst_stex_tp": "KRX",  # 국내거래소
                "acctNo": acct_no
            }
            res_json, headers = self.request_api(
                endpoint="/api/dostk/acnt",
                method="POST",
                data=body,
                api_id="kt00018",
                cont_yn=cont_yn,
                next_key=next_key
            )
            
            if res_json.get("return_code", 0) != 0:
                raise Exception(f"API Error: {res_json.get('return_msg')}")

            # 계좌 요약 수치는 첫 페이지 기준으로 파싱
            if not summary_data:
                summary_data = {
                    "tot_pur_amt": res_json.get("tot_pur_amt", "0"),
                    "tot_evlt_amt": res_json.get("tot_evlt_amt", "0"),
                    "tot_evlt_pl": res_json.get("tot_evlt_pl", "0"),
                    "tot_prft_rt": res_json.get("tot_prft_rt", "0"),
                    "prsm_dpst_aset_amt": res_json.get("prsm_dpst_aset_amt", "0")
                }

            holdings = res_json.get("stk_cntr_remn", [])
            all_holdings.extend(holdings)

            # 연속조회 여부 및 키 추출 (헤더 또는 바디)
            cont_yn = headers.get("cont-yn", "N")
            next_key = headers.get("next-key", "")

            if cont_yn != "Y" or not next_key:
                break

        summary_data["stk_cntr_remn"] = all_holdings
        return summary_data
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_client_queries.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add client.py tests/test_client_queries.py
git commit -m "feat: add get_accounts and get_balance with pagination to KiwoomClient"
```

---

### Task 4: CLI Application & Output Presentation (`cli.py`)

**Files:**
- Create: `cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `ConfigManager`, `KiwoomClient`
- Produces: CLI 실행 가능한 `cli.py` 파일

- [ ] **Step 1: Write the failing test**

Create: `tests/test_cli.py`
```python
import os
import json
import tempfile
from click.testing import CliRunner
import requests_mock
from cli import main

def test_cli_balance_command(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Given: 임시 config 파일 생성
        config_data = {
            "users": {
                "user1": {
                    "appkey": "key",
                    "secretkey": "sec"
                }
            }
        }
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        # 토큰 캐시 파일 생성
        tokens_data = {
            "user1": {
                "token": "valid_token",
                "expires_dt": "20360101000000"
            }
        }
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # API Mocking
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", json={
            "return_code": 0,
            "tot_pur_amt": "1000000",
            "tot_evlt_amt": "1200000",
            "tot_evlt_pl": "200000",
            "tot_prft_rt": "20.00",
            "prsm_dpst_aset_amt": "1500000",
            "stk_cntr_remn": [
                {
                    "stk_cd": "A005930",
                    "stk_nm": "삼성전자",
                    "rmnd_qty": "10",
                    "pur_pric": "50000",
                    "cur_prc": "60000",
                    "evltv_prft": "100000",
                    "pl_rt": "20.00"
                }
            ]
        })

        # When: Click CliRunner 실행
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--user", "user1",
            "balance",
            "--acct", "1234567890"
        ])

        # Then: 결과 가독성 검증
        assert result.exit_code == 0
        assert "계좌 평가 현황" in result.output
        assert "삼성전자" in result.output
        assert "1,000,000" in result.output # 천단위 콤마 포맷팅 검증
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with "ImportError: cannot import name 'main' from 'cli'"

- [ ] **Step 3: Write minimal implementation**

Create: `cli.py`
```python
import click
import os
from config import ConfigManager
from client import KiwoomClient

def format_currency(val):
    try:
        return f"{int(float(val)):,}"
    except (ValueError, TypeError):
        return val

def format_percent(val):
    try:
        val_float = float(val)
        sign = "+" if val_float > 0 else ""
        return f"{sign}{val_float:.2f}%"
    except (ValueError, TypeError):
        return val

@click.group()
@click.option("--config-dir", default=None, help="Directory path containing config.json")
@click.option("--user", "-u", required=True, help="User ID to query")
@click.pass_context
def main(ctx, config_dir, user):
    """Kiwoom REST API CLI Tool"""
    # config manager 초기화 및 context 전달
    cm = ConfigManager(base_dir=config_dir)
    ctx.obj = {
        "user_id": user,
        "config_manager": cm
    }

@main.command()
@click.pass_context
def accounts(ctx):
    """Enquire accounts connected to the user token"""
    user_id = ctx.obj["user_id"]
    cm = ctx.obj["config_manager"]
    client = KiwoomClient(user_id=user_id, config_manager=cm)
    
    try:
        accts = client.get_accounts()
        click.echo(f"=== [{user_id}] 계좌 목록 ===")
        for idx, acct in enumerate(accts, 1):
            click.echo(f" {idx}. 계좌번호: {acct}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@main.command()
@click.option("--acct", default=None, help="Specific account number to query")
@click.pass_context
def balance(ctx, acct):
    """Enquire portfolio balance and details of the account"""
    user_id = ctx.obj["user_id"]
    cm = ctx.obj["config_manager"]
    client = KiwoomClient(user_id=user_id, config_manager=cm)

    try:
        # 계좌 지정이 안되었으면 첫 계좌 자동 선택
        if not acct:
            accts = client.get_accounts()
            if not accts:
                click.echo("Error: 연결된 계좌가 없습니다.", err=True)
                return
            acct = accts[0]

        res = client.get_balance(acct)
        
        click.echo("\n" + "=" * 50)
        click.echo(f"  [{user_id}] 계좌 평가 현황")
        click.echo("=" * 50)
        click.echo(f"계좌 번호   : {acct}")
        click.echo(f"추정예탁자산 : {format_currency(res.get('prsm_dpst_aset_amt'))} 원")
        click.echo(f"총 매입금액  : {format_currency(res.get('tot_pur_amt'))} 원")
        click.echo(f"총 평가금액  : {format_currency(res.get('tot_evlt_amt'))} 원")
        click.echo(f"총 평가손익  : {format_currency(res.get('tot_evlt_pl'))} 원")
        click.echo(f"총 수익률    : {format_percent(res.get('tot_prft_rt'))}")
        click.echo("=" * 50)

        holdings = res.get("stk_cntr_remn", [])
        if not holdings:
            click.echo("\n보유 주식이 없습니다.")
            return

        click.echo("\n" + "=" * 90)
        click.echo(f"  [{user_id}] 보유 종목 현황")
        click.echo("=" * 90)
        # 테이블 헤더 포맷팅
        click.echo(f"{'종목코드':<8} | {'종목명':<16} | {'보유수량':<8} | {'매입단가':<10} | {'현재가':<10} | {'평가손익':<12} | {'수익률':<8}")
        click.echo("-" * 90)
        
        for stock in holdings:
            code = stock.get("stk_cd", "").replace("A", "") # 접두사 'A' 제거하여 표시
            name = stock.get("stk_nm", "")
            qty = f"{int(float(stock.get('rmnd_qty', 0)))} 주"
            pur_uv = f"{format_currency(stock.get('pur_pric'))} 원"
            cur_prc = f"{format_currency(stock.get('cur_prc'))} 원"
            pl_amt = format_currency(stock.get('evltv_prft'))
            pl_amt_str = f"+{pl_amt}" if float(stock.get('evltv_prft', 0)) > 0 else pl_amt
            pl_rt = format_percent(stock.get('pl_rt'))
            
            click.echo(f"{code:<8} | {name:<16} | {qty:<8} | {pur_uv:<10} | {cur_prc:<10} | {pl_amt_str:>12} | {pl_rt:>8}")
        click.echo("=" * 90)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cli.py tests/test_cli.py
git commit -m "feat: implement Click CLI user interfaces and output formatting"
```
