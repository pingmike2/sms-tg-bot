#!/usr/bin/env python3
# 检查 turnstile 容器尺寸为0的根因（祖先链 + 视口）
import json, time, urllib.request
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
tgt = [t for t in tabs if t["type"] == "page" and "sign-up" in t.get("url", "")][0]
ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=60)
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
print("viewport:", ev("JSON.stringify({w:innerWidth,h:innerHeight,dpr:devicePixelRatio})"))
print("\n=== 祖先链尺寸 ===")
print(ev("""(() => {
  let el = document.querySelector('.cf-turnstile');
  const out = [];
  for (let i=0; el && i<8; i++) {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    out.push(`${el.tagName}.${(el.className||'').toString().slice(0,30)} ${Math.round(r.width)}x${Math.round(r.height)} disp=${s.display} overflow=${s.overflow}`);
    el = el.parentElement;
  }
  return out.join('\\n');
})()"""))
print("\n=== turnstile.widgets / 状态 ===")
print(ev("""(() => {
  try {
    return JSON.stringify({
      hasRender: typeof turnstile.render,
      widgets: (turnstile.getAllWidgets ? turnstile.getAllWidgets().length : 'n/a')
    });
  } catch(e) { return 'ERR '+e.message; }
})()"""))
print("\n=== 容器 innerHTML (前400) ===")
print(str(ev("(document.querySelector('.cf-turnstile')||{}).innerHTML"))[:400])
print("\n=== 是否有 turnstile 隐藏 iframe ===")
print(ev("""(() => {
  const fr = document.querySelectorAll('iframe');
  return 'iframe count=' + fr.length;
})()"""))
ws.close()
