import os
import json
import tempfile
import pytest
from kiwoom.config import ConfigManager

def test_config_manager_load_and_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_data = {
            "accounts": {
                "1234567890": {
                    "appkey": "key123",
                    "secretkey": "sec123"
                }
            }
        }
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump(config_data, f)

        cm = ConfigManager(base_dir=tmpdir)

        creds = cm.load_credentials("1234567890")
        assert creds == {"appkey": "key123", "secretkey": "sec123"}

        with pytest.raises(KeyError):
            cm.load_credentials("non_exist_account")

        cm.save_token("1234567890", "token_val", "20260620120000")
        token_info = cm.load_token("1234567890")
        assert token_info == {"token": "token_val", "expires_dt": "20260620120000"}

def test_config_manager_corrupted_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        tokens_path = os.path.join(tmpdir, "tokens.json")
        with open(tokens_path, "w", encoding="utf-8") as f:
            f.write("{corrupted_json...")

        cm = ConfigManager(base_dir=tmpdir)

        token_info = cm.load_token("1234567890")
        assert token_info == {}

        cm.save_token("1234567890", "new_token", "20260620120000")
        token_info = cm.load_token("1234567890")
        assert token_info["token"] == "new_token"


def test_config_manager_legacy_users_key():
    with tempfile.TemporaryDirectory() as tmpdir:
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

        with pytest.raises(KeyError) as excinfo:
            cm.load_credentials("1234567890")
        assert "기존 'users' 형식의 설정이 감지되었습니다" in str(excinfo.value)

