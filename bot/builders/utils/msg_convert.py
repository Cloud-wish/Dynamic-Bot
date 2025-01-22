from __future__ import annotations
import base64

def msg_convert(content: str, file_image: bytes | None) -> list[dict[str]]:
    msg = []
    if(len(content)):
        msg.append({
            "type": "text",
            "data": {"text": content}
        })
    if type(file_image) is bytes:
        msg.append({
            "type": "image",
            "data": {
                "file": "base64://" + base64.b64encode(file_image).decode('utf-8')
            }
        })
    return msg