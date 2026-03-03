from __future__ import annotations

import json
from app.core import user_store

def main() -> None:
    path = user_store.USERS_FILE
    print("USERS_FILE =", path)
    print("exists    =", path.exists())

    if path.exists():
        raw = path.read_bytes()
        print("bytes len =", len(raw))
        print("starts with BOM =", raw.startswith(b"\xef\xbb\xbf"))
        print("first 20 bytes =", raw[:20])

        # JSONとして読めるか（BOM対策含めてチェック）
        try:
            text = raw.decode("utf-8")
            json.loads(text)
            print("json.loads(utf-8) = OK")
        except Exception as e:
            print("json.loads(utf-8) = NG:", repr(e))

        try:
            text_sig = raw.decode("utf-8-sig")  # BOM除去してdecode
            json.loads(text_sig)
            print("json.loads(utf-8-sig) = OK (BOM除去)")
        except Exception as e:
            print("json.loads(utf-8-sig) = NG:", repr(e))

    users = user_store.load_users()
    print("load_users count =", len(users))
    if users:
        print("ids =", [u.get("id") for u in users])

    u = user_store.get_user("12414")
    print("get_user('12414') =", "FOUND" if u else "NOT FOUND")
    if u:
        print("stored password len =", len(u.get("password","")))
        print("stored password =", u.get("password",""))

if __name__ == "__main__":
    main()