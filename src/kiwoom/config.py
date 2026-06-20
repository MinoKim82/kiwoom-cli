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

    def load_credentials(self, account):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        accounts = data.get("accounts", {})
        if not accounts and "users" in data:
            raise KeyError(
                "기존 'users' 형식의 설정이 감지되었습니다. "
                "계좌 기반('accounts') 설정 형식으로 업데이트가 필요합니다."
            )
        if account not in accounts:
            raise KeyError(f"Account {account} not found in configuration.")
        return accounts[account]

    def load_token(self, account):
        if not os.path.exists(self.tokens_path):
            return {}
        with open(self.tokens_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return {}
        return data.get(account, {})

    def save_token(self, account, token, expires_dt):
        data = {}
        if os.path.exists(self.tokens_path):
            with open(self.tokens_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        data[account] = {
            "token": token,
            "expires_dt": expires_dt
        }
        with open(self.tokens_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_all_account_aliases(self) -> list:
        if not os.path.exists(self.config_path):
            return []
        with open(self.config_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return []
        return list(data.get("accounts", {}).keys())

