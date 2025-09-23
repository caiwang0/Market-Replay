import os
import time
import requests
import app.config as config
import app.models.api.auth as auth
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import JSONResponse
import json
import uuid
import base64
import hashlib
import logging
import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

LARK_APP_ID     = config.LARK_APP_ID
LARK_APP_SECRET = config.LARK_APP_SECRET
LARK_BASE_URL = config.LARK_BASE_URL

# Internal cache
_lark_tenant_token   = None
_lark_token_expires  = 0

# Debugging purposes
log = logging.getLogger("app.api.lark.routes")

# =============================================================================
# Authentication Token
# =============================================================================
def get_lark_tenant_token() -> str:
    global _lark_tenant_token, _lark_token_expires

    # Refresh 60s before real expiry
    if not _lark_tenant_token or time.time() >= _lark_token_expires - 60:
        url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal/"
        resp = requests.post(
            url,
            json={"app_id": config.LARK_APP_ID, "app_secret": config.LARK_APP_SECRET},
            headers={"Content-Type": "application/json"}
        )
        data = resp.json()
        if resp.status_code != 200 or data.get("code") != 0:
            raise RuntimeError(f"Failed to fetch tenant token: {data}")
        _lark_tenant_token = data["tenant_access_token"]
        # `expire` is in seconds
        _lark_token_expires = time.time() + data.get("expire", 7200)

    return _lark_tenant_token

# =============================================================================
# Send Magic Link
# =============================================================================
def get_lark_user_id(token: str, json: dict) -> list:
    # Initialize headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    # Send a post request for user_ids of Gotrade lark users
    resp = requests.post(
        f"{config.LARK_BASE_URL}/open-apis/contact/v3/users/batch_get_id",
        json=json,
        headers=headers
    )

    # Raise an exception if response fails
    if resp.status_code != 200:
        raise HTTPException(502, "Error querying Lark API")
    users = resp.json().get("data", {}).get("user_list", [])

    # Raise exception if user does not exist
    if not users or not users[0].get("user_id"):
        raise HTTPException(404, "Email not found in GoTrade Lark workspace")
    
    # Return user id whose email matches
    return users[0]["user_id"]

def send_lark_magic_link_message(lark_user_id: str, token: str, data: auth.TokenRequest, verify_token: str) -> requests.Response:
    # Initialize headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    # Build magic-link URL
    magic_link = (
        f"{config.HOST_NAME + config.FE_PATH_PREFIX}"
        f"/verify?email={data.email}&verifyToken={verify_token}"
    )

    # Initialize json
    json = {
        "receive_id_type": "open_id",
        "open_id": lark_user_id,
        "msg_type": "text",
        "content": {"text": f"🔑 Click here to log in:\n\n{magic_link}"},
    }

    # Send the magic link through Lark messages
    chat_resp = requests.post(
        f"{config.LARK_BASE_URL}/open-apis/message/v4/send/",
        headers=headers,
        json=json,
    )

    # Parse the JSON response and check against Lark’s code field
    body = chat_resp.json()
    if body.get("code") != 0:
        # Return a 502 with Lark error
        raise HTTPException(
            status_code=502,
            detail=f"Lark error {body.get('code')}: {body.get('msg')}"
        )

    return JSONResponse({"status": "ok"})

# =============================================================================
# Get Lark Base View
# =============================================================================
def get_lark_base_view(token, app_token, table_token, view_token=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }
    resp = requests.get(f"{config.LARK_BASE_URL}/open-apis/bitable/v1/apps/{app_token}/tables/{table_token}/views/{view_token}", headers=headers)

    # Raise an exception if response fails
    if resp.status_code != 200:
        raise HTTPException(502, "Error querying Lark API")
    
    if resp.json().get("code") != 0:
        raise HTTPException(502, f"Lark API error: {resp.json().get('msg', 'Unknown error')}")

    # Parse the JSON response and return the view data
    base_view_data = resp.json()
    return base_view_data
# =============================================================================
# Get Lark Base Table Records
# =============================================================================
def get_lark_base_table_records(token, app_token, table_token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }  

    resp = requests.get(f"{config.LARK_BASE_URL}/open-apis/bitable/v1/apps/{app_token}/tables/{table_token}/records", headers=headers)

    # Raise an exception if response fails
    if resp.status_code != 200:
        raise HTTPException(502, "Error querying Lark API")
    
    if resp.json().get("code") != 0:
        raise HTTPException(502, f"Lark API error: {resp.json().get('msg', 'Unknown error')}")
    
    # Parse the JSON response and return the records
    base_table_records = resp.json()
    return base_table_records
# =============================================================================
# Get Lark Docx Raw Content
# =============================================================================
def get_lark_docx_raw_content(token, document_token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }  

    resp = requests.get(f"{config.LARK_BASE_URL}/open-apis/docx/v1/documents/{document_token}/raw_content", headers=headers)
    
    # Raise an exception if response fails
    if resp.status_code != 200:
        raise HTTPException(502, "Error querying Lark API")
    
    if resp.json().get("code") != 0:
        raise HTTPException(502, f"Lark API error: {resp.json().get('msg', 'Unknown error')}")
    
    # Parse the JSON response and return the raw content
    raw_content = resp.json().get("data", {}).get("content")
    return raw_content

# =============================================================================
# Decrypt lark payload
# =============================================================================

def decrypt_lark_payload(encrypt: str, encrypt_key: str) -> str:
    # 1) Build AES key from encrypt_key (sha256)
    key = hashlib.sha256(encrypt_key.strip().encode("utf-8")).digest()  # 32 bytes
    raw = base64.b64decode(encrypt.replace(" ", "+"))  # defend against space->+ issues

    # 2) IV = first 16 bytes of ciphertext, rest is real ciphertext
    iv, ct = raw[:16], raw[16:]
    if len(ct) % 16 != 0:
        log.error("Ciphertext length not block aligned: %d", len(ct))

    # 3) Decrypt + PKCS7 unpad
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ct)
    try:
        plaintext = unpad(decrypted, AES.block_size, style="pkcs7").decode("utf-8")
    except ValueError:
        log.error("PKCS7 unpad failed. last_byte=%d tail=%r", decrypted[-1], decrypted[-16:])
        raise
    return plaintext

# =============================================================================
# Send lark message to user
# =============================================================================

async def send_lark_message(user_id: str, msg_type: str, content: dict):
    LARK_MESSAGE_URL = "https://open.larksuite.com/open-apis/im/v1/messages"
    token = get_lark_tenant_token()
    if not token:
        return {"status": "error", "detail": "Failed to get access token"}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "receive_id": user_id,
        "msg_type": msg_type,                         
        "content": json.dumps(content),       
        "uuid": str(uuid.uuid4())
    }
    params = {"receive_id_type": "user_id"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(LARK_MESSAGE_URL, params=params, headers=headers, json=payload)
        data = resp.json()
        return {"status": "sent"} if data.get("code") == 0 else {"status": "error", "detail": data}

# =============================================================================
# Extract user_id
# =============================================================================
def extract_user_id(payload: dict) -> str | None:
    sender_id = payload.get("event", {}).get("sender", {}).get("sender_id", {})
    return sender_id.get("user_id") or sender_id.get("open_id") or sender_id.get("union_id")