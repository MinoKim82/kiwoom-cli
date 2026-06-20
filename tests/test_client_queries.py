import pytest
import requests_mock
from kiwoom.client import KiwoomClient

class MockConfigManager:
    def load_credentials(self, account):
        return {"appkey": "key", "secretkey": "sec"}
    def load_token(self, account):
        return {"token": "valid_token", "expires_dt": "20360101000000"}

def test_get_account_info(requests_mock):
    cm = MockConfigManager()
    client = KiwoomClient(account="mh_default", config_manager=cm, host="https://mockapi.kiwoom.com")

    requests_mock.post(
        "https://mockapi.kiwoom.com/api/dostk/acnt",
        json={
            "acctNo": "1234567890",
            "acctNm": "홍길동",
            "acctTpNm": "위탁종합",
            "return_code": 0
        }
    )

    info = client.get_account_info()
    assert info == {
        "acctNo": "1234567890",
        "acctNm": "홍길동",
        "acctTpNm": "위탁종합",
        "return_code": 0
    }

    # Test get_accounts delegating to cached get_account_info
    accounts = client.get_accounts()
    assert accounts == ["1234567890"]

def test_get_balance_pagination(requests_mock):
    cm = MockConfigManager()
    client = KiwoomClient(account="mh_default", config_manager=cm, host="https://mockapi.kiwoom.com")

    # Mock for get_accounts() inside get_balance() when acct_no is None
    # It calls /api/dostk/acnt for account list first
    requests_mock.post(
        "https://mockapi.kiwoom.com/api/dostk/acnt",
        [
            {
                "json": {
                    "acctNo": "1234567890",
                    "return_code": 0
                },
                "status_code": 200
            },
            {
                "json": {
                    "tot_pur_amt": "10000",
                    "acnt_evlt_remn_indv_tot": [{"stk_cd": "A005930", "stk_nm": "삼성전자"}],
                    "return_code": 0
                },
                "headers": {"cont-yn": "Y", "next-key": "page2_key"},
                "status_code": 200
            },
            {
                "json": {
                    "tot_pur_amt": "10000",
                    "acnt_evlt_remn_indv_tot": [{"stk_cd": "A000660", "stk_nm": "SK하이닉스"}],
                    "return_code": 0
                },
                "headers": {"cont-yn": "N", "next-key": ""},
                "status_code": 200
            }
        ]
    )

    balance = client.get_balance()
    assert balance["acct_no"] == "1234567890"
    assert len(balance["acnt_evlt_remn_indv_tot"]) == 2
    assert balance["acnt_evlt_remn_indv_tot"][0]["stk_nm"] == "삼성전자"
    assert balance["acnt_evlt_remn_indv_tot"][1]["stk_nm"] == "SK하이닉스"
    assert balance["tot_pur_amt"] == "10000"


def test_get_balance_with_explicit_acct(requests_mock):
    cm = MockConfigManager()
    client = KiwoomClient(account="mh_default", config_manager=cm, host="https://mockapi.kiwoom.com")

    # Mock balance API only (get_accounts is bypassed)
    requests_mock.post(
        "https://mockapi.kiwoom.com/api/dostk/acnt",
        json={
            "tot_pur_amt": "5000",
            "acnt_evlt_remn_indv_tot": [{"stk_cd": "A005930", "stk_nm": "삼성전자"}],
            "return_code": 0
        }
    )

    balance = client.get_balance(acct_no="9876543210")
    assert balance["acct_no"] == "9876543210"
    assert balance["tot_pur_amt"] == "5000"


