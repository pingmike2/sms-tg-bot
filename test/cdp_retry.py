#!/usr/bin/env python3
# 重新加载页面，等 turnstile 渲染出来（容器非 0 尺寸）
import json, time, urllib.request
import websocket

def newtab(url):
    req = urllib.request.Request(f"http://127.0.0.1:9222/json/new?{url}", method="PUT")
    return json.load(urllib.request.urlopen(req, timeout=15))

t = newtab("about:blank")
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

send("Page.enable"); send("Runtime.enable")
# 设置桌面视口
send("Emulation.setDeviceMetricsOverride", width=1400, height=900, deviceScaleFactor=1, mobile=False)
send("Page.navigate", url="https://temp-number.com/sign-up")

for i in range(20):
    time.sleep(2)
    sz = ev("""(() => {
      const c = document.querySelector('.cf-turnstile');
      if (!c) return 'no-container';
      const r = c.getBoundingClientRect();
      return `${Math.round(r.width)}x${Math.round(r.height)}`;
    })()""")
    tok = ev("""(() => { const e=document.querySelector('[name="cf-turnstile-response"]'); return e?e.value.length:-1 })()""")
    title = ev("document.title")
    print(f"t+{2*(i+1)}s size={sz} tokenLen={tok} title={str(title)[:30]}")
    if isinstance(sz, str) and "x" in sz:
        w, h = sz.split("x")
        if int(w) > 0 and int(h) > 0:
            print(">>> 容器已渲染")
            break
        if tok and isinstance(tok, int) and tok > 20:
            break

print("\niframes:", ev("""(() => [...document.querySelectorAll('iframe')].map(f=>f.src.slice(0,80)).join('\\n')||'none')()"""))
ws.close()
