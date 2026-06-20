# Kiwoom CLI JSON Output Format Option Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CLI 프로그램에 `--format` / `-f` 글로벌 옵션을 추가하고, `json` 포맷을 지정했을 시 계좌 정보와 평가 잔고를 기계가 가공하기 좋은 JSON 규격으로 출력하도록 기능을 확장합니다.

**Architecture:**
- **글로벌 옵션 추가**: `cli.py` 내의 `@click.group()` 데코레이터 하위에 `--format` 옵션을 추가하고, `click.Choice(["text", "json"])` 타입(기본값 "text")으로 지정합니다.
- **명령어 동작 변경**: 
  - `accounts`: `format`이 `json`일 때 `{"accounts": [...]}` 형식으로 JSON을 출력합니다.
  - `balance`: `format`이 `json`일 때 `{"user_id": ..., "acct_no": ..., "balance": {...}}` 형태로 전체 스냅샷 JSON을 출력합니다.
- **TDD 검증**: 신규 JSON 옵션 관련 유닛 테스트를 추가하여 테스트가 성공하는지 확인합니다.

**Tech Stack:**
- Python 3
- `click`, `json` (표준 라이브러리)
- `pytest`, `requests-mock` (테스트 의존성)

## Global Constraints
- 기존의 사람이 보기 좋게 출력하는 텍스트 포맷팅("text")도 기본값으로서 완벽히 하방 호환성을 유지해야 합니다.
- 테스트 시, `pytest`를 통해 새롭게 추가한 JSON 출력 모드가 오류 없이 작동하고 검증되는지 파싱 여부를 확인합니다.

---

### Task 1: CLI Format Option Implementation & Verification

**Files:**
- Modify: `src/kiwoom/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `--format json` 옵션 추가 및 CLI JSON 출력 지원

- [ ] **Step 1: Write the failing tests**

Modify: `tests/test_cli.py` (파일 하단에 추가)
```python
def test_cli_accounts_json_format(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Given: config.json 및 tokens.json 생성
        config_data = {"users": {"user1": {"appkey": "key", "secretkey": "sec"}}}
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {"user1": {"token": "valid_token", "expires_dt": "20360101000000"}}
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # API Mocking
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", json={
            "acctNo": "1234567890",
            "return_code": 0
        })

        # When: Click CliRunner 실행 (--format json 지정)
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--user", "user1",
            "--format", "json",
            "accounts"
        ])

        # Then: 결과가 JSON 형태인지 검증
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed == {"accounts": ["1234567890"]}

def test_cli_balance_json_format(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Given: config.json 및 tokens.json 생성
        config_data = {"users": {"user1": {"appkey": "key", "secretkey": "sec"}}}
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {"user1": {"token": "valid_token", "expires_dt": "20360101000000"}}
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
            "acnt_evlt_remn_indv_tot": [
                {
                    "stk_cd": "A005930",
                    "stk_nm": "삼성전자",
                    "rmnd_qty": "10",
                    "pur_pric": "50000",
                    "cur_prc": "60000",
                    "evltv_prft": "100000",
                    "prft_rt": "20.00"
                }
            ]
        })

        # When: Click CliRunner 실행 (--format json 지정)
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--user", "user1",
            "--format", "json",
            "balance",
            "--acct", "1234567890"
        ])

        # Then: 결과가 JSON 형태인지 검증
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["user_id"] == "user1"
        assert parsed["acct_no"] == "1234567890"
        assert parsed["balance"]["tot_pur_amt"] == "1000000"
        assert len(parsed["balance"]["acnt_evlt_remn_indv_tot"]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -k "json_format"`
Expected: FAIL due to click parsing error (no such option `--format`) or missing assertion checks.

- [ ] **Step 3: Modify cli.py implementation**

Modify: `src/kiwoom/cli.py`
Add `--format` / `-f` parameter, and implement JSON formatting condition for `accounts` and `balance` commands.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest`
Expected: PASS (all 12 passed)

- [ ] **Step 5: Commit changes**

```bash
git add src/kiwoom/cli.py tests/test_cli.py
git commit -m "feat: add --format option to CLI for parsing JSON output"
```
