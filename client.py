import requests
from datetime import datetime, timedelta


class KiwoomClient:
    def __init__(self, user_id, config_manager, host="https://api.kiwoom.com"):
        self.user_id = user_id
        self.config_manager = config_manager
        self.host = host

    def get_valid_token(self):
        token_info = self.config_manager.load_token(self.user_id)
        token = token_info.get("token")
        expires_dt_str = token_info.get("expires_dt")

        refresh_needed = True
        if token and expires_dt_str:
            try:
                # KST 시간으로 저장된 expires_dt 파싱
                expires_at = datetime.strptime(expires_dt_str, "%Y%m%d%H%M%S")
                # 현재 로컬 시간 기준 만료까지 10분 이상 남았는지 체크
                if expires_at - datetime.now() > timedelta(minutes=10):
                    refresh_needed = False
                    return token
            except ValueError:
                pass

        if refresh_needed:
            creds = self.config_manager.load_credentials(self.user_id)
            token_url = f"{self.host}/oauth2/token"
            headers = {"Content-Type": "application/json;charset=UTF-8"}
            body = {
                "grant_type": "client_credentials",
                "appkey": creds["appkey"],
                "secretkey": creds["secretkey"]
            }
            res = requests.post(token_url, headers=headers, json=body)
            res.raise_for_status()
            res_json = res.json()
            
            if res_json.get("return_code", 0) != 0:
                raise Exception(f"Failed to issue token (code: {res_json.get('return_code')}): {res_json.get('return_msg')}")
                
            new_token = res_json["token"]
            new_expires = res_json["expires_dt"]
            self.config_manager.save_token(self.user_id, new_token, new_expires)
            return new_token

    def request_api(self, endpoint, method="POST", data=None, api_id=None, cont_yn="N", next_key="") -> tuple[dict, dict]:
        token = self.get_valid_token()
        url = f"{self.host}{endpoint}"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {token}",
            "cont-yn": cont_yn,
            "next-key": next_key
        }
        if api_id:
            headers["api-id"] = api_id

        if method == "POST":
            res = requests.post(url, headers=headers, json=data or {})
        else:
            res = requests.get(url, headers=headers, params=data)
        
        res.raise_for_status()

        try:
            res_json = res.json()
        except ValueError:
            res_json = {}

        if res_json.get("return_code", 0) != 0:
            raise Exception(f"API Error (code: {res_json.get('return_code')}): {res_json.get('return_msg')}")

        return res_json, res.headers
