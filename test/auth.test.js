// 离线鉴权测试：不起网络，验证 /setup、/tg 路径、secret 头、OWNER_ID 白名单
// 用法：node test/auth.test.js
const fs = require("fs");
const path = require("path");
const os = require("os");

const src = fs.readFileSync(path.join(__dirname, "../worker.js"), "utf8");
const tmp = path.join(os.tmpdir(), `smsbot_auth_${process.pid}.mjs`);
fs.writeFileSync(tmp, src);

let fail = 0;
const ok = (name, cond, extra = "") => {
  if (cond) console.log(`✅ ${name}`);
  else { console.log(`❌ ${name} ${extra}`); fail++; }
};

// 拦截所有出站 fetch：Telegram API 一律回 ok，接码站回空页，避免联网
const realFetch = globalThis.fetch;
let tgCalls = [];
globalThis.fetch = async (input, init) => {
  const url = typeof input === "string" ? input : input.url;
  if (url.includes("api.telegram.org")) {
    const method = url.split("/").pop();
    let body = {};
    try { body = JSON.parse(init?.body || "{}"); } catch { body = {}; }
    tgCalls.push({ method, body });
    return new Response(JSON.stringify({ ok: true, result: { message_id: 1 } }), {
      headers: { "content-type": "application/json" },
    });
  }
  return new Response("<html></html>", { status: 200 });
};

const env = {
  BOT_TOKEN: "123:TESTTOKEN",
  OWNER_ID: "123456789",
  WEBHOOK_SECRET: "s3cret",
};

const BASE = "https://bot.example";
const call = (pathname, opts = {}, e = env) =>
  worker.fetch(new Request(BASE + pathname, opts), e, { waitUntil: () => {} });

let worker;
(async () => {
  try {
    worker = (await import("file://" + tmp)).default;
  } catch (e) {
    console.log("❌ worker.js 无法加载:", e.message);
    process.exit(1);
  }

  // ---- /setup 鉴权 ----
  let r = await call("/setup");
  ok("/setup 无 x-setup-token → 403", r.status === 403, `得到 ${r.status}`);

  r = await call("/setup", { headers: { "x-setup-token": "wrong" } });
  ok("/setup 错误 token → 403", r.status === 403, `得到 ${r.status}`);

  tgCalls = [];
  r = await call("/setup", { headers: { "x-setup-token": "s3cret" } });
  ok("/setup 正确 token → 200", r.status === 200, `得到 ${r.status}`);
  ok("/setup 调用了 setWebhook", tgCalls.some((c) => c.method === "setWebhook"), JSON.stringify(tgCalls.map((c) => c.method)));
  const sw = tgCalls.find((c) => c.method === "setWebhook");
  ok("setWebhook 带 secret_token", sw?.body?.secret_token === "s3cret", JSON.stringify(sw?.body?.secret_token));
  ok("setWebhook url 含 /tg/<token>", String(sw?.body?.url || "").includes("/tg/123:TESTTOKEN"), String(sw?.body?.url));

  // ---- WEBHOOK_SECRET 未配置 ----
  const envNoSecret = { ...env, WEBHOOK_SECRET: "" };
  r = await call("/setup", { headers: { "x-setup-token": "" } }, envNoSecret);
  ok("未配 WEBHOOK_SECRET → 500", r.status === 500, `得到 ${r.status}`);

  // ---- /tg 路径鉴权 ----
  const upd = (from) => ({
    method: "POST",
    headers: { "content-type": "application/json", "x-telegram-bot-api-secret-token": "s3cret" },
    body: JSON.stringify({ message: { message_id: 1, chat: { id: from }, from: { id: from }, text: "/start" } }),
  });

  r = await call("/tg/WRONGBOTTOKEN", upd(123456789));
  ok("/tg 错误 BOT_TOKEN → 403", r.status === 403, `得到 ${r.status}`);

  r = await worker.fetch(
    new Request(BASE + "/tg/123:TESTTOKEN", {
      method: "POST",
      headers: { "content-type": "application/json", "x-telegram-bot-api-secret-token": "WRONG" },
      body: JSON.stringify({ message: { message_id: 1, chat: { id: 123456789 }, from: { id: 123456789 }, text: "/start" } }),
    }),
    env,
    { waitUntil: () => {} }
  );
  ok("secret 头错误 → 403", r.status === 403, `得到 ${r.status}`);

  r = await call("/tg/123:TESTTOKEN", { method: "GET", headers: { "x-telegram-bot-api-secret-token": "s3cret" } });
  ok("/tg GET → 404（只认 POST）", r.status === 404, `得到 ${r.status}`);

  // ---- OWNER_ID 白名单 ----
  tgCalls = [];
  await call("/tg/123:TESTTOKEN", upd(999999999));
  const answer = tgCalls.find((c) => c.method === "sendMessage");
  ok("非主人被拒（有回包说明收到处理）", !!answer, JSON.stringify(tgCalls.map((c) => c.method)));
  ok("非主人回复含「私有」", /私有/.test(JSON.stringify(answer?.body || {})), JSON.stringify(answer?.body || {}).slice(0, 120));

  tgCalls = [];
  await call("/tg/123:TESTTOKEN", upd(123456789));
  const mine = tgCalls.find((c) => c.method === "sendMessage");
  ok("主人收到 /start 回包", !!mine, JSON.stringify(tgCalls.map((c) => c.method)));
  ok("主人回包不含「私有」", !/私有/.test(JSON.stringify(mine?.body || {})));

  // ---- /health ----
  r = await call("/health");
  const body = await r.text();
  ok("/health 200 且含 sites=", r.status === 200 && /sites=\d+/.test(body), body);

  fs.unlinkSync(tmp);
  globalThis.fetch = realFetch;
  console.log(fail === 0 ? "\n全部通过" : `\n${fail} 项失败`);
  process.exit(fail === 0 ? 0 : 1);
})();
