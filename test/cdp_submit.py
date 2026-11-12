#!/usr/bin/env python3
# step1：填密码 + 勾条款 + 等 Turnstile，然后提交
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
        return "EXC: " + str(res["exceptionDetails"].get("exception", {}).get("description", ""))[:150]
    return res.get("result", {}).get("value")

send("Runtime.enable")
PW = "TempNumber2026"
p = json.dumps({"password": PW, "password_confirmation": PW})
print("填密码:", ev("""
(() => {
  const v = %s;
  const setter = (el, val) => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el, val);
    ['input','change','blur'].forEach(e => el.dispatchEvent(new Event(e,{bubbles:true})));
  };
  const done=[];
  for (const [k,val] of Object.entries(v)) {
    const el=document.querySelector(`[name="${k}"]`);
    if(el){setter(el,val);done.push(k);}
  }
  return done.join(',');
})()
""" % p))
print("密码长度校验:", ev("""(() => JSON.stringify({
  pw: (document.querySelector('[name=password]')||{}).value.length,
  pw2: (document.querySelector('[name=password_confirmation]')||{}).value.length
}))()"""))

print("勾条款:", ev("""(() => {
  const t = document.querySelector('[name="terms"]');
  if (!t) return 'none';
  if (!t.checked) t.click();
  return 'checked=' + t.checked;
})()"""))

# 检查 turnstile iframe
print("iframes:", ev("""(() => document.querySelectorAll('iframe').length)()"""))
print("turnstile ready:", ev("typeof turnstile"))

for i in range(25):
    time.sleep(3)
    tok = ev("""(() => { const e=document.querySelector('[name="cf-turnstile-response"]'); return e?(e.value||'').length:-1 })()""")
    print(f"  t+{3*(i+1)}s tokenLen={tok}")
    if isinstance(tok, int) and tok > 20:
        print(">>> Turnstile 已通过！token=", ev("""(() => document.querySelector('[name="cf-turnstile-response"]').value.slice(0,40))()"""))
        break

print("\n=== 提交 ===")
print(ev("""(() => {
  const b = [...document.querySelectorAll('button')].find(x =>
    x.getBoundingClientRect().height>0 && /Create Account|Sign up|Register/i.test(x.innerText));
  if (!b) return 'no submit btn';
  b.click();
  return 'clicked: ' + b.innerText.trim();
})()"""))
time.sleep(10)
print("\n=== 提交后 URL ===")
print(ev("location.href"))
print("=== 页面文本 ===")
print((ev("document.body.innerText") or "")[:500].replace("\n", " | "))
ws.close()
