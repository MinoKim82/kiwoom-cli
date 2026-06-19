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


def test_request_api_post(requests_mock):
    class MockConfigManager:
        def load_credentials(self, user_id):
            return {"appkey": "my_appkey", "secretkey": "my_secretkey"}
        def load_token(self, user_id):
            # 만료되지 않은 토큰
            valid_time = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
            return {"token": "valid_token", "expires_dt": valid_time}
        def save_token(self, user_id, token, expires_dt):
            pass

    mcm = MockConfigManager()
    client = KiwoomClient(user_id="user1", config_manager=mcm, host="https://mockapi.kiwoom.com")

    # POST API 모킹
    requests_mock.post(
        "https://mockapi.kiwoom.com/v1/mock-endpoint",
        json={"result": "success"},
        headers={"resp-header": "value"}
    )

    # API 호출
    res_data, res_headers = client.request_api(
        endpoint="/v1/mock-endpoint",
        method="POST",
        data={"param1": "value1"},
        api_id="mock_api_id",
        cont_yn="Y",
        next_key="12345"
    )

    # 검증
    assert res_data == {"result": "success"}
    assert res_headers.get("resp-header") == "value"

    # 전송된 요청의 헤더 및 바디 검증
    last_request = requests_mock.last_request
    assert last_request.headers.get("authorization") == "Bearer valid_token"
    assert last_request.headers.get("cont-yn") == "Y"
    assert last_request.headers.get("next-key") == "12345"
    assert last_request.headers.get("api-id") == "mock_api_id"
    assert last_request.json() == {"param1": "value1"}


def test_request_api_get(requests_mock):
    class MockConfigManager:
        def load_credentials(self, user_id):
            return {"appkey": "my_appkey", "secretkey": "my_secretkey"}
        def load_token(self, user_id):
            valid_time = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
            return {"token": "valid_token", "expires_dt": valid_time}
        def save_token(self, user_id, token, expires_dt):
            pass

    mcm = MockConfigManager()
    client = KiwoomClient(user_id="user1", config_manager=mcm, host="https://mockapi.kiwoom.com")

    # GET API 모킹
    requests_mock.get(
        "https://mockapi.kiwoom.com/v1/mock-endpoint",
        json={"result": "success"}
    )

    # API 호출
    res_data, res_headers = client.request_api(
        endpoint="/v1/mock-endpoint",
        method="GET",
        data={"param1": "value1"}
    )

    # 검증
    assert res_data == {"result": "success"}

    # 전송된 요청의 헤더 및 쿼리 파라미터 검증
    last_request = requests_mock.last_request
    assert last_request.headers.get("authorization") == "Bearer valid_token"
    assert last_request.qs == {"param1": ["value1"]}

