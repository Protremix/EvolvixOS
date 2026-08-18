import hmac
import hashlib
import base64
import zlib
import json
import time
import urllib.request
import urllib.parse
import random
import os

class TIMIntegration:
    """Tencent IM (TIMSDK) REST API integration for EvolvixOS.
    
    Requires SDKAppID and SecretKey from Tencent Cloud Chat console.
    Create a free app at: https://console.trtc.io
    """

    def __init__(self, sdk_app_id=None, secret_key=None):
        self.sdk_app_id = sdk_app_id or os.environ.get("TIM_SDK_APP_ID", "")
        self.secret_key = secret_key or os.environ.get("TIM_SECRET_KEY", "")
        self.api_base = "https://adminapiger.im.qcloud.com"
        self.admin_identifier = "evolvix_admin"

    def gen_usersig(self, identifier, expire=86400):
        """Generate UserSig using HMAC-SHA256."""
        if not self.secret_key:
            return None
        curr_time = int(time.time())
        sig_doc = {
            "TLS.sig_ver": "sha256",
            "TLS.identifier": str(identifier),
            "TLS.sdk_appid": str(self.sdk_app_id),
            "TLS.expire": expire,
            "TLS.time": curr_time,
        }
        sig_doc = dict(sorted(sig_doc.items()))
        sig_str = json.dumps(sig_doc, separators=(",", ":"))
        compressed = zlib.compress(sig_str.encode("utf-8"))
        mac = hmac.new(self.secret_key.encode("utf-8"), compressed, hashlib.sha256)
        sig = mac.digest()
        sig_base64 = base64.b64encode(sig).decode("utf-8")
        sig_doc["TLS.sig"] = sig_base64
        sig_str = json.dumps(sig_doc, separators=(",", ":"))
        encoded = sig_str.encode("utf-8")
        compressed2 = zlib.compress(encoded)
        final = base64.b64encode(compressed2).decode("utf-8")
        final = final.replace("+", "*").replace("/", "-").replace("=", "_")
        return final

    def call_api(self, service, command, body=None):
        """Call a TIM REST API endpoint."""
        if not self.sdk_app_id or not self.secret_key:
            return {"error": "TIM not configured. Set TIM_SDK_APP_ID and TIM_SECRET_KEY."}
        usersig = self.gen_usersig(self.admin_identifier)
        if not usersig:
            return {"error": "Failed to generate UserSig"}
        rand = random.randint(0, 4294967295)
        url = f"{self.api_base}/v4/{service}/{command}?sdkappid={self.sdk_app_id}&identifier={self.admin_identifier}&usersig={usersig}&random={rand}&contenttype=json"
        data = json.dumps(body or {}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def send_message(self, to_user, content, msg_type="text"):
        if msg_type == "text":
            msg_body = [{"MsgType": "TIMTextElem", "MsgContent": {"Text": content}}]
        else:
            msg_body = [{"MsgType": "TIMCustomElem", "MsgContent": {"Data": content}}]
        return self.call_api("openim", "admin_sendmsg", {
            "SyncOtherMachine": 1,
            "From_Account": self.admin_identifier,
            "To_Account": to_user,
            "MsgLifeTime": 604800,
            "MsgBody": msg_body,
        })

    def import_account(self, user_id, nickname=""):
        return self.call_api("im_open_login_svc", "account_import", {
            "Identifier": user_id,
            "Nick": nickname,
            "Type": 0,
        })

    def create_group(self, group_name, group_type="Public"):
        return self.call_api("group_open_http_svc", "create_group", {
            "Name": group_name,
            "Type": group_type,
        })

    def send_group_message(self, group_id, content):
        return self.call_api("group_open_http_svc", "send_group_msg", {
            "GroupId": group_id,
            "Random": random.randint(0, 4294967295),
            "MsgBody": [{"MsgType": "TIMTextElem", "MsgContent": {"Text": content}}],
        })

    def get_user_list(self, limit=100):
        return self.call_api("im_open_login_svc", "get_user_list", {
            "Start": 0,
            "Limit": limit,
        })

    def is_configured(self):
        return bool(self.sdk_app_id and self.secret_key)


if __name__ == "__main__":
    tim = TIMIntegration()
    if tim.is_configured():
        print("TIM configured:", tim.sdk_app_id)
    else:
        print("TIM not configured. Set TIM_SDK_APP_ID and TIM_SECRET_KEY env vars.")
