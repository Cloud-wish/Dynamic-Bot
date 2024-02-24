from datetime import datetime, timedelta, timezone

def msg_preprocess(data: dict, typ: str) -> dict:
    if("created_time" in data and type(data["created_time"]) == int):
        data["created_time"] = datetime.fromtimestamp(data["created_time"], tz=timezone(timedelta(hours=+8))).strftime("%Y-%m-%d %H:%M:%S")
    user = data.get("user", {})
    if not "name" in user:
        data["user"]["name"] = "[未知用户名]"
    if("retweet" in data):
        data["retweet"] = msg_preprocess(data["retweet"], typ)
    if("reply" in data):
        data["reply"] = msg_preprocess(data["reply"], typ)
    if("root" in data):
        data["root"] = msg_preprocess(data["root"], typ)
    return data