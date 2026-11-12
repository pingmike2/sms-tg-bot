#!/usr/bin/env python3
# 手动 render turnstile widget（容器已可见），再等 token
import json, time, urllib.request
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
tgt = [t for t in tabs if t["type"] == "page" and "sign-up" in t.get("url", "")][0]
ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=180)
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
        return "EXC: " + str(res["exceptionDetails"].get("exception", {}).get("description", ""))[:200]
    return res.get("result", {}).get("value")

send("Runtime.enable")
# 确认还在 step1（可见）
print("step1 可见:", ev("""(() => {
  const s=[...document.querySelectorAll('.auth-step')].find(x=>getComputedStyle(x).display!=='none');
  return s ? s.getBoundingClientRect().height : -1;
})()"""))

print("容器:", ev("""(() => { const c=document.querySelector('.cf-turnstile');
  const r=c.getBoundingClientRect(); return Math.round(r.width)+'x'+Math.round(r.height); })()"""))

# 手动 render，带 try
print("render:", ev("""(() => {
  try {
    const c = document.querySelector('.cf-turnstile');
    if (!c) return 'no container';
    // 清空旧内容
    c.innerHTML = '';
    const sk = '0x4AAAAAAAGhGJU0btRzc26Z';
    const id = turnstile.render(c, {
      sitekey: sk,
      theme: 'light',
      callback: (t) => { window.__tok = t; window.__tsOk = true; },
      'error-callback': (e) => { window.__tErr = String(e); }
    });
    return 'rendered widgetId=' + id;
  } catch(e) { return 'ERR: ' + e.message; }
})()"""))
time.sleep(5)
print("iframes:", ev("document.querySelectorAll('iframe').length"))
print("err:", ev("window.__tErr || 'none'"))

for i in range(20):
    time.sleep(3)
    tok = ev("window.__tok || ''")
    hidden = ev("""(() => { const e=document.querySelector('[name="cf-turnstile-response"]'); return e?(e.value||'').length:-1 })()""")
    print(f"  t+{3*(i+1)}s cbToken={len(tok) if isinstance(tok,str) else 0} hiddenLen={hidden}")
    if isinstance(tok, str) and len(tok) > 20:
        print(">>> 通过！", tok[:50])
        break
print("页尾:", (ev("document.body.innerText") or "")[-150:].replace("\n"," | "))
ws.close()
