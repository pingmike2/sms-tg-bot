#!/usr/bin/env python3
# 用 CDP 填表并提交 temp-number 注册（修正转义）
import json, time, urllib.request, sys
import websocket

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10))
target = None
for t in tabs:
    if t["type"] == "page" and "sign-up" in t.get("url", ""):
        target = t
        break
if not target:
    req = urllib.request.Request("http://127.0.0.1:9222/json/new?https://temp-number.com/sign-up", method="PUT")
    target = json.load(urllib.request.urlopen(req, timeout=10))
    time.sleep(10)

ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=90)
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
    res = r.get("result", {})
    if "exceptionDetails" in res:
        return "EXC: " + str(res["exceptionDetails"].get("exception", {}).get("description", ""))[:200]
    return res.get("result", {}).get("value")

send("Runtime.enable")
print("title:", ev("document.title"))

mb = json.load(open("/tmp/mailtm.json"))
EMAIL = mb["address"]
PW = "TempNumber2026"

# 逐字段用 JSON.stringify 注入，避免引号问题
payload = json.dumps({"full_name": "Alex Carter", "email": EMAIL,
                      "password": PW, "password_confirmation": PW})
fill = """
(() => {
  const v = %s;
  const setter = (el, val) => {
    const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    set.call(el, val);
    ['input','change','blur'].forEach(e => el.dispatchEvent(new Event(e, {bubbles:true})));
  };
  const done = [];
  for (const [k,val] of Object.entries(v)) {
    const el = document.querySelector(`[name="${k}"]`);
    if (el) { setter(el, val); done.push(k); }
  }
  return done.join(',') || 'NONE';
})()
""" % payload
print("filled:", ev(fill))

print("values:", ev("""(() => JSON.stringify({
  name: (document.querySelector('[name=full_name]')||{}).value,
  email: (document.querySelector('[name=email]')||{}).value,
  pwLen: ((document.querySelector('[name=password]')||{}).value||'').length,
  pw2Len: ((document.querySelector('[name=password_confirmation]')||{}).value||'').length
}))()"""))

print("terms:", ev("""(() => {
  const t = document.querySelector('[name="terms"]');
  if (!t) return 'none';
  if (!t.checked) t.click();
  return 'checked=' + t.checked;
})()"""))

for i in range(10):
    time.sleep(3)
    n = ev("(() => { const e=document.querySelector('[name=\"cf-turnstile-response\"]'); return e?e.value.length:-1 })()")
    print(f"  t+{3*(i+1)}s turnstile token len = {n}")
    if isinstance(n, int) and n > 20:
        break

print("body:", (ev("document.body.innerText") or "")[:150].replace("\n", " | "))
ws.close()
