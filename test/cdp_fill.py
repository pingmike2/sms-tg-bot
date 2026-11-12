#!/usr/bin/env python3
# 在有头浏览器里填 temp-number 注册表单
import json, time, urllib.request
import websocket

def http_put(path):
    req = urllib.request.Request(f"http://127.0.0.1:9222{path}", method="PUT")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

tab = http_put("/json/new?about:blank")
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=90)
_id = [0]
def send(method, **params):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id[0]:
            return msg

def ev(expr):
    r = send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
    res = r.get("result", {}).get("result", {})
    if "exceptionDetails" in r.get("result", {}):
        return "EXC: " + str(r["result"]["exceptionDetails"])[:150]
    return res.get("value")

send("Page.enable"); send("Runtime.enable")
send("Page.navigate", url="https://temp-number.com/sign-up")
time.sleep(10)
print("title:", ev("document.title"))
print("hasForm:", ev("!!document.querySelector('#registerForm')"))

mb = json.load(open("/tmp/mailtm.json"))
EMAIL = mb["address"]
PW = "TempNumber2026!"

# 填入字段（触发 React/Vue 需要的 input+change 事件）
fill = """
(() => {
  const setter = (el, val) => {
    const proto = el.tagName === 'INPUT' ? HTMLInputElement.prototype : el.prototype;
    const set = Object.getOwnPropertyDescriptor(proto, 'value').set;
    set.call(el, val);
    el.dispatchEvent(new Event('input', {bubbles:true}));
    el.dispatchEvent(new Event('change', {bubbles:true}));
    el.dispatchEvent(new Event('blur', {bubbles:true}));
  };
  const q = n => document.querySelector(`[name="${n}"]`);
  let done = [];
  if (q('full_name')) { setter(q('full_name'), 'Alex Carter'); done.push('name'); }
  if (q('email')) { setter(q('email'), EMAIL); done.push('email'); }
  if (q('password')) { setter(q('password'), PW); done.push('pw'); }
  if (q('password_confirmation')) { setter(q('password_confirmation'), PW); done.push('pw2'); }
  return done.join(',');
})()
""".replace('EMAIL', EMAIL).replace('PW', PW)
print("filled:", ev(fill))

# 勾选条款
print("terms:", ev("""(() => {
  const t = document.querySelector('[name="terms"]');
  if (!t) return 'no terms field';
  if (!t.checked) t.click();
  return 'checked=' + t.checked;
})()"""))

time.sleep(8)
print("turnstile token len:", ev("""(() => {
  const e = document.querySelector('[name="cf-turnstile-response"]');
  return e ? e.value.length : -1;
})()"""))
print("page text:", (ev("document.body.innerText") or "")[:200].replace("\n", " | "))
ws.close()
