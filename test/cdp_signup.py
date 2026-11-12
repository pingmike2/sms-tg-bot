#!/usr/bin/env python3
# 通过 CDP 用有头浏览器操作 temp-number 注册
import json, time, urllib.request, urllib.parse
import websocket

def http(path):
    with urllib.request.urlopen(f"http://127.0.0.1:9222{path}", timeout=10) as r:
        return json.loads(r.read())

# 新建标签页
t = http("/json/new?about:blank") if False else None
# 用 PUT 建标签
req = urllib.request.Request("http://127.0.0.1:9222/json/new?about:blank", method="PUT")
with urllib.request.urlopen(req, timeout=10) as r:
    tab = json.loads(r.read())
ws_url = tab["webSocketDebuggerUrl"]
print("tab:", tab["id"])

ws = websocket.create_connection(ws_url, timeout=60)
_id = [0]
def send(method, **params):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id[0]:
            return msg

send("Page.enable")
send("Runtime.enable")
send("Page.navigate", url="https://temp-number.com/sign-up")
time.sleep(12)

def ev(expr):
    r = send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
    return r.get("result", {}).get("result", {}).get("value")

print("title:", ev("document.title"))
print("webdriver:", ev("navigator.webdriver"))
print("ua:", ev("navigator.userAgent")[:90])
print("hasForm:", ev("!!document.querySelector('#registerForm')"))
print("turnstileInput:", ev("!!document.querySelector('[name=\"cf-turnstile-response\"]')"))
print("turnstileReady:", ev("(()=>{const e=document.querySelector('[name=\"cf-turnstile-response\"]');return e? e.value.length : -1})()"))
print("bodyText:", (ev("document.body.innerText") or "")[:300].replace("\n", " | "))
ws.close()
