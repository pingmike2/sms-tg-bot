#!/usr/bin/env python3
# 直接导航到 rch 挑战 URL，看渲染内容
import json, time, urllib.request
import websocket

req = urllib.request.Request("http://127.0.0.1:9222/json/new?about:blank", method="PUT")
t = json.load(urllib.request.urlopen(req, timeout=10))
ws = websocket.create_connection(t["webSocketDebuggerUrl"], timeout=120)
_id = [0]
def send(method, **params):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params}))
    while True:
        m = json.loads(ws.recv())
        if m.get("id") == _id[0]:
            return m
def ev(e):
    r = send("Runtime.evaluate", expression=e, returnByValue=True, awaitPromise=True)
    res = r.get("result", {})
    if "exceptionDetails" in res:
        return "EXC"
    return res.get("result", {}).get("value")

send("Page.enable"); send("Runtime.enable"); send("Network.enable")
url = "https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/g/turnstile/f/av0/rch/5wcgz/0x4AAAAAAAGhGJU0btRzc26Z/light"
send("Page.navigate", url=url)
time.sleep(10)
print("URL:", ev("location.href")[:140])
print("title:", ev("document.title"))
print("body len:", ev("document.body.innerHTML.length"))
print("body:", (ev("document.body.innerText") or "")[:300].replace("\n", " | "))
print("html head:", (ev("document.documentElement.outerHTML") or "")[:400])
ws.close()
