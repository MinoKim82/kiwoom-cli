import os
import json
import tempfile
from click.testing import CliRunner
import requests_mock
from kiwoom.cli import main

def test_cli_info_command(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {"accounts": {"mh_default": {"appkey": "key", "secretkey": "sec"}}}
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {"mh_default": {"token": "valid_token", "expires_dt": "20360101000000"}}
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", json={
            "acctNo": "1234567810",
            "acctNm": "홍길동",
            "acctTpNm": "위탁종합",
            "return_code": 0
        })

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--account", "mh_default",
            "info"
        ])

        assert result.exit_code == 0
        assert "=== [mh_default] 계좌 정보 ===" in result.output
        assert "계좌번호: 12345678" in result.output
        assert "계좌명: 홍길동" in result.output
        assert "상품구분: 위탁종합" in result.output

def test_cli_balance_command(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {"accounts": {"mh_default": {"appkey": "key", "secretkey": "sec"}}}
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {"mh_default": {"token": "valid_token", "expires_dt": "20360101000000"}}
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # First post mock for get_accounts inside balance
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", [
            {
                "json": {
                    "acctNo": "1234567810",
                    "return_code": 0
                },
                "status_code": 200
            },
            {
                "json": {
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
                },
                "status_code": 200
            }
        ])

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--account", "mh_default",
            "balance"
        ])

        assert result.exit_code == 0
        assert "계좌 평가 현황" in result.output
        assert "[12345678] 계좌 평가 현황" in result.output  # Display actual account number
        assert "삼성전자" in result.output
        assert "1,000,000" in result.output

def test_cli_balance_json_format(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {"accounts": {"mh_default": {"appkey": "key", "secretkey": "sec"}}}
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {"mh_default": {"token": "valid_token", "expires_dt": "20360101000000"}}
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", [
            {
                "json": {
                    "acctNo": "1234567810",
                    "return_code": 0
                },
                "status_code": 200
            },
            {
                "json": {
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
                },
                "status_code": 200
            }
        ])

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--account", "mh_default",
            "--format", "json",
            "balance"
        ])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["account"] == "mh_default"
        assert parsed["acct_no"] == "1234567810"  # Verify actual account number in json
        assert parsed["balance"]["tot_pur_amt"] == "1000000"
        assert len(parsed["balance"]["acnt_evlt_remn_indv_tot"]) == 1


def test_cli_balance_with_specific_acct(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {"accounts": {"mh_default": {"appkey": "key", "secretkey": "sec"}}}
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {"mh_default": {"token": "valid_token", "expires_dt": "20360101000000"}}
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # Mock balance API only, since get_accounts is bypassed when --acct is specified
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

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--account", "mh_default",
            "--format", "json",
            "balance",
            "--acct", "9876543210"
        ])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["account"] == "mh_default"
        assert parsed["acct_no"] == "9876543210"
        # Check that request sent specified account number
        last_request = requests_mock.last_request
        assert last_request.json()["acctNo"] == "9876543210"
def test_cli_info_all_accounts(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {
            "accounts": {
                "mh_default": {"appkey": "key", "secretkey": "sec"},
                "mh_sub": {"appkey": "key2", "secretkey": "sec2"}
            }
        }
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {
            "mh_default": {"token": "valid_token1", "expires_dt": "20360101000000"},
            "mh_sub": {"token": "valid_token2", "expires_dt": "20360101000000"}
        }
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # Mock account responses for both aliases
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", [
            {"json": {"acctNo": "1234567810", "acctNm": "홍길동", "acctTpNm": "위탁종합", "return_code": 0}},
            {"json": {"acctNo": "9876543204", "acctNm": "이몽룡", "acctTpNm": "위탁종합", "return_code": 0}}
        ])

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "info"
        ])

        assert result.exit_code == 0
        assert "=== [mh_default] 계좌 정보 ===" in result.output
        assert "계좌번호: 12345678" in result.output
        assert "상품구분: 위탁종합" in result.output
        assert "=== [mh_sub] 계좌 정보 ===" in result.output
        assert "계좌번호: 98765432" in result.output
        assert "상품구분: 위탁종합" in result.output

def test_cli_balance_all_accounts_json(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {
            "accounts": {
                "mh_default": {"appkey": "key", "secretkey": "sec"},
                "mh_sub": {"appkey": "key2", "secretkey": "sec2"}
            }
        }
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {
            "mh_default": {"token": "valid_token1", "expires_dt": "20360101000000"},
            "mh_sub": {"token": "valid_token2", "expires_dt": "20360101000000"}
        }
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # Mock API endpoints in sequence:
        # 1. mh_default get_accounts()
        # 2. mh_default get_balance()
        # 3. mh_sub get_accounts()
        # 4. mh_sub get_balance()
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", [
            {"json": {"acctNo": "1234567810", "return_code": 0}},
            {"json": {"acctNo": "1234567810", "tot_pur_amt": "1000", "acnt_evlt_remn_indv_tot": [], "return_code": 0}},
            {"json": {"acctNo": "9876543204", "return_code": 0}},
            {"json": {"acctNo": "9876543204", "tot_pur_amt": "2000", "acnt_evlt_remn_indv_tot": [], "return_code": 0}}
        ])

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--format", "json",
            "balance"
        ])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["account"] == "mh_default"
        assert parsed[0]["acct_no"] == "1234567810"
        assert parsed[0]["balance"]["tot_pur_amt"] == "1000"
        assert parsed[1]["account"] == "mh_sub"
        assert parsed[1]["acct_no"] == "9876543204"
        assert parsed[1]["balance"]["tot_pur_amt"] == "2000"

def test_cli_balance_single_account_error(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {"accounts": {"mh_default": {"appkey": "key", "secretkey": "sec"}}}
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {"mh_default": {"token": "valid_token", "expires_dt": "20360101000000"}}
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # Mock API to return failure in get_accounts
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", status_code=500, text="Internal Server Error")

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--account", "mh_default",
            "balance"
        ])

        # For a single account query, failure should immediately exit with code 1
        assert result.exit_code == 1
        assert "500 Server Error" in result.output

        # Check JSON format exit code and output structure as well
        result_json = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--account", "mh_default",
            "--format", "json",
            "balance"
        ])
        assert result_json.exit_code == 1
        parsed = json.loads(result_json.output)
        assert "error" in parsed

def test_cli_balance_all_accounts_with_partial_error(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {
            "accounts": {
                "mh_default": {"appkey": "key", "secretkey": "sec"},
                "mh_sub": {"appkey": "key2", "secretkey": "sec2"}
            }
        }
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {
            "mh_default": {"token": "valid_token1", "expires_dt": "20360101000000"},
            "mh_sub": {"token": "valid_token2", "expires_dt": "20360101000000"}
        }
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # Mock APIs:
        # mh_default: get_accounts (success), get_balance (success)
        # mh_sub: get_accounts (failure status 500)
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", [
            {"json": {"acctNo": "1234567810", "return_code": 0}},
            {"json": {"acctNo": "1234567810", "tot_pur_amt": "1000", "acnt_evlt_remn_indv_tot": [], "return_code": 0}},
            {"status_code": 500, "text": "API Error"}
        ])

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--format", "json",
            "balance"
        ])

        # Multi-account queries must isolate errors and not abort. So exit_code is 0.
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

        # First account: success
        assert parsed[0]["account"] == "mh_default"
        assert parsed[0]["acct_no"] == "1234567810"
        assert parsed[0]["balance"]["tot_pur_amt"] == "1000"

        # Second account: failure
        assert parsed[1]["account"] == "mh_sub"
        assert parsed[1]["acct_no"] == "mh_sub"
        assert "error" in parsed[1]["balance"]
        assert "500 Server Error" in parsed[1]["balance"]["error"]

def test_cli_balance_all_accounts_with_partial_error_text(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {
            "accounts": {
                "mh_default": {"appkey": "key", "secretkey": "sec"},
                "mh_sub": {"appkey": "key2", "secretkey": "sec2"}
            }
        }
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {
            "mh_default": {"token": "valid_token1", "expires_dt": "20360101000000"},
            "mh_sub": {"token": "valid_token2", "expires_dt": "20360101000000"}
        }
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # Mock APIs:
        # mh_default: get_accounts (success), get_balance (success)
        # mh_sub: get_accounts (failure status 500)
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", [
            {"json": {"acctNo": "1234567810", "return_code": 0}},
            {"json": {"acctNo": "1234567810", "tot_pur_amt": "1000", "acnt_evlt_remn_indv_tot": [], "return_code": 0}},
            {"status_code": 500, "text": "API Error"}
        ])

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "balance"
        ])

        # Text mode should also complete with exit code 0
        assert result.exit_code == 0
        # First account shows success output
        assert "[12345678] 계좌 평가 현황" in result.output
        # Second account shows failure message
        assert "[mh_sub] 계좌 잔고 조회 실패: 500 Server Error" in result.output

def test_cli_subcommand_format_override(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {"accounts": {"mh_default": {"appkey": "key", "secretkey": "sec"}}}
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {"mh_default": {"token": "valid_token", "expires_dt": "20360101000000"}}
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        # Mock API for get_accounts and get_balance
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", [
            {"json": {"acctNo": "1234567810", "return_code": 0}},
            {"json": {"acctNo": "1234567810", "tot_pur_amt": "7777", "acnt_evlt_remn_indv_tot": [], "return_code": 0}}
        ])

        runner = CliRunner()
        
        # 1. Test balance command with -f json option placed AFTER the command
        result_bal = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--account", "mh_default",
            "balance",
            "-f", "json"
        ])
        assert result_bal.exit_code == 0
        parsed_bal = json.loads(result_bal.output)
        assert parsed_bal["account"] == "mh_default"
        assert parsed_bal["balance"]["tot_pur_amt"] == "7777"

        # Mock API for get_account_info
        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", json={
            "acctNo": "1234567810",
            "acctNm": "홍길동",
            "acctTpNm": "위탁종합",
            "return_code": 0
        })

        # 2. Test info command with --format json option placed AFTER the command
        result_info = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--account", "mh_default",
            "info",
            "--format", "json"
        ])
        assert result_info.exit_code == 0
        parsed_info = json.loads(result_info.output)
        assert parsed_info["account_alias"] == "mh_default"
        assert parsed_info["account_info"]["acctNm"] == "홍길동"
