// 本地端到端：真打 tempsmss.com，拦截 Telegram API 调用并打印
const fs = require("fs");
const path = require("path");

const src = fs.readFileSync(path.join(__dirname, "../src/worker.js"), "utf8");
const mod = src.replace("export default {", "module.exports = {") + "\n";
const tmp = path.join(__dirname, "_w.cjs");
fs.writeFileSync(tmp, mod);
const worker = require(tmp);

const calls = [];
const realFetch = globalThis.fetch;
globalThis.fetch = async (input, init) => {
  const url = typeof input === "string" ? input : input.url;
  if (url.includes("api.telegram.org")) {
    const body = JSON.parse(init.body || "{}");
    calls.push({ method: url.split("/").pop(), body });
    return new Response(JSON.stringify({ ok: true, result: { message_id: 1 } }), { headers: { "content-type": "application/json" } });
  }
  return realFetch(input, init);
};

const env = {
  BOT_TOKEN: "123:TEST",
  OWNER_ID: "7870073609",
  WEBHOOK_SECRET: "s3cret",
  UPSTREAM: "https://tempsmss.com",
};

async function run(label, update) {
  calls.length = 0;
  const pending = [];
  await worker.fetch(
    new Request("https://bot.example/tg/123:TEST", {
      method: "POST",
      headers: { "content-type": "application/json", "x-telegram-bot-api-secret-token": "s3cret" },
      body: JSON.stringify(update),
    }),
    env,
    { waitUntil: (p) => pending.push(p) }
  );
  await Promise.all(pending);
  console.log("=====", label);
  for (const c of calls) {
    console.log(`[${c.method}]`, JSON.stringify(c.body).slice(0, 1200));
  }
  if (!calls.length) console.log("(无回包)");
}

const msg = (text) => ({ message: { message_id: 1, chat: { id: 7870073609 }, from: { id: 7870073609 }, text } });

(async () => {
  await run("非主人", { message: { message_id: 2, chat: { id: 1 }, from: { id: 999 }, text: "hi" } });
  await run("/start", msg("/start"));
  await run("US 列表", msg("🇺🇸 US"));
  await run("点号码未命中缓存(slug)", { callback_query: { id: "q", from: { id: 7870073609 }, message: { chat: { id: 7870073609 } }, data: "n:us-otp-verification-code-818" } });
  await run("搜 openai", msg("openai"));
  await run("贴号码", msg("+19898885938"));
})().catch((e) => console.error("FATAL", e));
