#!/usr/bin/env python3
# 点“单击此处验证”按钮，让阿里云验证码渲染出来
import json, time, urllib.request
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
tgt = [t for t in tabs if t["type"] == "page" and "wetalkapp" in t.get("url", "")][0]
ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=200)
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
        return "EXC: " + str(res["exceptionDetails"].get("exception", {}).get("description", ""))[:120]
    return res.get("result", {}).get("value")

send("Runtime.enable")
print("按钮:", ev("""(() => {
  const b = [...document.querySelectorAll('.custom-btn')].map(x => x.innerText.trim());
  return JSON.stringify(b);
})()"""))
print("点击:", ev("""(() => {
  const b = document.querySelector('.custom-btn');
  if (!b) return 'no btn';
  b.click();
  return 'clicked';
})()"""))
time.sleep(6)
print("\n验证码容器:", ev("""(() => {
  const c = document.querySelector('#aliyunCaptcha');
  if (!c) return 'none';
  const r = c.getBoundingClientRect();
  return Math.round(r.width)+'x'+Math.round(r.height)+' | children='+c.children.length;
})()"""))
print("iframe:", ev("""(() => [...document.querySelectorAll('iframe')].map(f=>f.src.slice(0,80)).join('\\n')||'none')()"""))
print("页面是否有滑块:", ev("""(() => {
  const t = document.body.innerText;
  return /拖动|滑块|验证|slide/i.test(t) ? 'maybe' : 'no';
})()"""))
ws.close()
