#!/usr/bin/env python3
# 查看 turnstile iframe 内部状态（尝试跨域访问受限时的降级：看尺寸+网络）
import json, time, urllib.request
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
tgt = [t for t in tabs if t["type"] == "page" and "sign-up" in t.get("url", "")][0]
ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=120)
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

send("Runtime.enable")
print("iframe src:", ev("""(() => [...document.querySelectorAll('iframe')].map(f=>f.src.slice(0,120)).join('\\n'))()"""))
print("iframe size:", ev("""(() => [...document.querySelectorAll('iframe')].map(f=>{const r=f.getBoundingClientRect();return Math.round(r.width)+'x'+Math.round(r.height)}).join(','))()"""))

# 通过 CDP 拿到 iframe 的执行上下文
targets = send("Runtime.evaluate", expression="1")
frames = send("Page.getFrameTree")
print("\n=== frame tree ===")
def walk(f, d=0):
    print("  " * d + f["frame"]["url"][:110])
    for c in f.get("childFrames", []):
        walk(c, d + 1)
walk(frames["result"]["frameTree"])
ws.close()
