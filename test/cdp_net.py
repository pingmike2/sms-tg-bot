#!/usr/bin/env python3
# 抓到 turnstile 网络请求，看卡在哪
import json, time, urllib.request, threading
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
tgt = [t for t in tabs if t["type"] == "page" and "sign-up" in t.get("url", "")][0]
ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=300)
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
# 清事件并重新 render
ev("""(() => { window.__tErr2=null; return 1; })()""")
print("render:", ev("""(() => {
  try {
    const c = document.querySelector('.cf-turnstile');
    if (!c) return 'no container';
    const id = turnstile.render(c, {
      sitekey: '0x4AAAAAAAGhGJU0btRzc26Z',
      action: 'signup',
      theme: 'light',
      callback: t => { window.__tok2 = t; },
      'error-callback': e => { window.__tErr2 = String(e); }
    });
    return 'widget=' + id;
  } catch(e) { return 'ERR ' + e.message; }
})()"""))

# 收集 25 秒网络事件
deadline = time.time() + 25
ws.settimeout(2)
while time.time() < deadline:
    try:
        m = json.loads(ws.recv())
        if m.get("method"):
            events.append(m)
    except Exception:
        pass
ws.settimeout(300)

print("\n=== challenges.cloudflare.com 请求 ===")
for e in events:
    if e.get("method") in ("Network.requestWillBeSent", "Network.responseReceived", "Network.loadingFailed"):
        p = e["params"]
        url = (p.get("request", {}).get("url") or p.get("response", {}).get("url") or "")
        if "cloudflare.com" in url or "turnstile" in url or "challenge" in url:
            if e["method"] == "Network.requestWillBeSent":
                print("REQ ", url[:110])
            elif e["method"] == "Network.responseReceived":
                print("RESP", p["response"]["status"], url[:110])
            else:
                print("FAIL", p.get("errorText"), (p.get("requestId") or "")[:12])

print("\nerr:", ev("window.__tErr2 || 'none'"))
print("token:", ev("window.__tok2 ? window.__tok2.length : 0"))
print("iframes:", ev("document.querySelectorAll('iframe').length"))
ws.close()
