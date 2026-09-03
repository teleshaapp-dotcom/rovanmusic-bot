from pyrogram import Client

api_id = 35712521
api_hash = "b0713b67f41a77cb3271d49f84705d08" # (ئەگەر هاشەکەت گۆڕی، ئەمەش بگۆڕە)

with Client(":memory:", api_id=api_id, api_hash=api_hash) as app:
    session_string = app.export_session_string()
    print("\n🔑 کۆدی String Session ەکەت ئەمەیە:\n")
    print(session_string)
