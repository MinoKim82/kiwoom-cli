import os
import json
import tempfile
from click.testing import CliRunner
import requests_mock
from kiwoom.cli import main

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


def test_cli_accounts_json_error(requests_mock):
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
            "return_code": 999,
            "return_msg": "인증에 실패하였습니다."
        })

        # When: Click CliRunner 실행 (--format json 지정)
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--user", "user1",
            "--format", "json",
            "accounts"
        ])

        # Then: 결과가 JSON 형태의 에러인지 검증
        assert result.exit_code == 1
        parsed = json.loads(result.output)
        assert "error" in parsed
        assert "API Error (code: 999): 인증에 실패하였습니다." in parsed["error"]

