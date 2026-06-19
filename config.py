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

    def load_credentials(self, user_id):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        users = data.get("users", {})
        if user_id not in users:
            raise KeyError(f"User {user_id} not found in configuration.")
        return users[user_id]

    def load_token(self, user_id):
        if not os.path.exists(self.tokens_path):
            return {}
        with open(self.tokens_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return {}
        return data.get(user_id, {})

    def save_token(self, user_id, token, expires_dt):
        data = {}
        if os.path.exists(self.tokens_path):
            with open(self.tokens_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        data[user_id] = {
            "token": token,
            "expires_dt": expires_dt
        }
        with open(self.tokens_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
