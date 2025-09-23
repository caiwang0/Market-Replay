import os
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import json
from fastapi import HTTPException
import logging, asyncio
import app.services.lark as lark_service
import app.config as config

router = APIRouter()
log = logging.getLogger("app.api.lark.routes")

STANDARD_REPLY_MD = "Hi there! Please use the following link to access Sofi: [Sofi](http://ec2-108-136-238-112.ap-southeast-3.compute.amazonaws.com/agent/)"

STANDARD_CARD = {
    "config": {"wide_screen_mode": True},
    "elements": [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": STANDARD_REPLY_MD
            }
        }
    ]
}

async def handle_im_message(payload: dict):
    user_id = lark_service.extract_user_id(payload)
    if not user_id:
        log.warning("No user_id found in payload")
        return
    asyncio.create_task(lark_service.send_lark_message(user_id, "interactive", STANDARD_CARD))
    
# ---------- webhook ----------
@router.post("/webhook")
async def webhook(request: Request):
    body = await request.json()

    # Unencrypted challenge
    if "challenge" in body:
        return JSONResponse({"challenge": body["challenge"]}, 200)

    # Encrypted flow
    if "encrypt" in body:
        try:
            decrypted_str = lark_service.decrypt_lark_payload(body["encrypt"], config.LARK_ENCRYPT_KEY)
            decrypted = json.loads(decrypted_str)
        except Exception as e:
            log.exception("Decrypt/parse failed")
            raise HTTPException(status_code=400, detail=f"decrypt error: {e}")

        # Encrypted challenge
        if "challenge" in decrypted:
            return JSONResponse({"challenge": decrypted["challenge"]}, 200)

        # Real events
        event_type = decrypted.get("header", {}).get("event_type")
        if event_type == "im.message.receive_v1":
            await handle_im_message(decrypted)

        return JSONResponse({"code": 0, "msg": "ok"}, 200)
    
    return JSONResponse({"code": 0, "msg": "ignored"}, 200)