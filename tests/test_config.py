import os
import json
import tempfile
import pytest
from kiwoom.config import ConfigManager


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


def test_config_manager_corrupted_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a corrupted tokens.json file
        tokens_path = os.path.join(tmpdir, "tokens.json")
        with open(tokens_path, "w", encoding="utf-8") as f:
            f.write("{corrupted_json...")

        cm = ConfigManager(base_dir=tmpdir)

        # load_token should catch the JSONDecodeError and return {}
        token_info = cm.load_token("user1")
        assert token_info == {}

        # save_token should handle the corrupted file and successfully overwrite it
        cm.save_token("user1", "new_token", "20260620120000")
        token_info = cm.load_token("user1")
        assert token_info["token"] == "new_token"
