import pytest
import requests_mock
from client import KiwoomClient

class MockConfigManager:
    def load_credentials(self, user_id):
        return {"appkey": "key", "secretkey": "sec"}
    def load_token(self, user_id):
        return {"token": "valid_token", "expires_dt": "20360101000000"}

def test_get_accounts(requests_mock):
    cm = MockConfigManager()
    client = KiwoomClient(user_id="user1", config_manager=cm, host="https://mockapi.kiwoom.com")

    requests_mock.post(
        "https://mockapi.kiwoom.com/api/dostk/acnt",
        json={
            "acctNo": "1234567890",
            "return_code": 0
        }
    )

    accounts = client.get_accounts()
    assert accounts == ["1234567890"]

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
                    "stk_cntr_remn": [{"stk_cd": "A005930", "stk_nm": "삼성전자"}],
                    "return_code": 0
                },
                "headers": {"cont-yn": "Y", "next-key": "page2_key"},
                "status_code": 200
            },
            {
                "json": {
                    "tot_pur_amt": "10000",
                    "stk_cntr_remn": [{"stk_cd": "A000660", "stk_nm": "SK하이닉스"}],
                    "return_code": 0
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
    assert balance["tot_pur_amt"] == "10000"
