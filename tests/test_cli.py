import os
import json
import tempfile
from click.testing import CliRunner
import requests_mock
from kiwoom.cli import main

def test_cli_account_command(requests_mock):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {"accounts": {"mh_default": {"appkey": "key", "secretkey": "sec"}}}
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)
        
        tokens_data = {"mh_default": {"token": "valid_token", "expires_dt": "20360101000000"}}
        with open(os.path.join(tmpdir, "tokens.json"), "w") as f:
            json.dump(tokens_data, f)

        requests_mock.post("https://api.kiwoom.com/api/dostk/acnt", json={
            "acctNo": "1234567890",
            "return_code": 0
        })

        runner = CliRunner()
        result = runner.invoke(main, [
            "--config-dir", tmpdir,
            "--account", "mh_default",
            "account"
        ])

        assert result.exit_code == 0
        assert "=== [mh_default] 실제 계좌 목록 ===" in result.output
        assert "1234567890" in result.output

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
                    "acctNo": "1234567890",
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
        assert "[1234567890] 계좌 평가 현황" in result.output  # Display actual account number
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
                    "acctNo": "1234567890",
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
        assert parsed["acct_no"] == "1234567890"  # Verify actual account number in json
        assert parsed["balance"]["tot_pur_amt"] == "1000000"



