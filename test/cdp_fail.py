#!/usr/bin/env python3
# 监听网络失败，定位 turnstile iframe 加载为何报错
import json, time, urllib.request
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
tgt = [t for t in tabs if t["type"] == "page" and "sign-up" in t.get("url", "")][0]
ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=200)
_id = [0]
events = []
def send(method, **params):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params}))
    while True:
        m = json.loads(ws.recv())
        if m.get("method"):
            events.append(m)
        if m.get("id") == _id[0]:
            return m
def ev(e):
    r = send("Runtime.evaluate", expression=e, returnByValue=True, awaitPromise=True)
    res = r.get("result", {})
    if "exceptionDetails" in res:
        return "EXC"
    return res.get("result", {}).get("value")

send("Network.enable")
send("Runtime.enable")
# 删掉测试 iframe
ev("document.getElementById('t1')?.remove(); 1")

# 重新 render
print("render:", ev("""(() => {
  try {
    const c = document.querySelector('.cf-turnstile');
    c.innerHTML = '';
    window.__tok4 = null; window.__tErr4 = null;
    const id = turnstile.render(c, {
      sitekey: '0x4AAAAAAAGhGJU0btRzc26Z',
      callback: t => { window.__tok4 = t; },
      'error-callback': e => { window.__tErr4 = String(e); }
    });
    return id;
  } catch(e) { return 'ERR ' + e.message; }
})()"""))

ws.settimeout(2)
deadline = time.time() + 20
while time.time() < deadline:
    try:
        m = json.loads(ws.recv())
        if m.get("method"):
            events.append(m)
    except Exception:
        pass
ws.settimeout(200)

print("\n=== cloudflare 请求明细 ===")
for e in events:
    meth = e.get("method")
    p = e.get("params", {})
    if meth == "Network.requestWillBeSent":
        u = p["request"]["url"]
        if "cloudflare" in u:
            print("REQ ", u[:120])
    elif meth == "Network.responseReceived":
        u = p["response"]["url"]
        if "cloudflare" in u:
            print("RESP", p["response"]["status"], u[:120])
    elif meth == "Network.loadingFailed":
        print("FAIL", p.get("errorText"), "| blockedReason:", p.get("blockedReason"),
              "| cors:", p.get("corsErrorStatus", {}).get("corsError"))
    elif meth == "Network.requestServedFromCache":
        pass

print("\ntoken:", ev("window.__tok4 ? window.__tok4.length : 0"))
print("err:", ev("window.__tErr4 || 'none'"))
print("frame:", ev("document.querySelectorAll('iframe').length"))
ws.close()
