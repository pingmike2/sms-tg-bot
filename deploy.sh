#!/bin/bash
# 部署 tempsms-tg-bot 到 Cloudflare Workers
# 用法：先 export BOT_TOKEN / OWNER_ID，再 bash deploy.sh
set -e
cd "$(dirname "$0")"

# ---------- 必填（从环境变量传入，别写死在文件里）----------
# BOT_TOKEN   @BotFather 拿的 token，形如 123456:ABC...
# OWNER_ID    只允许这个人用，Telegram user id（找 @userinfobot 查）

if [ -z "$BOT_TOKEN" ]; then echo "缺少 BOT_TOKEN，先 export BOT_TOKEN='123456:ABC...'"; exit 1; fi
if [ -z "$OWNER_ID" ];  then echo "缺少 OWNER_ID，先 export OWNER_ID='你的telegram_id'";   exit 1; fi

export $(grep -E '^(CLOUDFLARE_API_TOKEN|CLOUDFLARE_ACCOUNT_ID)=' /root/.hermes/.env 2>/dev/null | xargs)

SECRET=$(openssl rand -hex 24)

echo "$BOT_TOKEN" | npx --yes wrangler@latest secret put BOT_TOKEN --name tempsms-tg-bot >/dev/null 2>&1
echo "$OWNER_ID"  | npx --yes wrangler@latest secret put OWNER_ID  --name tempsms-tg-bot >/dev/null 2>&1
echo "$SECRET"     | npx --yes wrangler@latest secret put WEBHOOK_SECRET --name tempsms-tg-bot >/dev/null 2>&1

BASE="https://tempsms-tg-bot.PLACEHOLDER.workers.dev"
curl -s "$BASE/setup" -o /tmp/setup.json -w 'setup HTTP=%{http_code}\n'
head -c 400 /tmp/setup.json
echo
# /setup 用的是 env.WEBHOOK_SECRET 回填 secret_token，需要等 secret 生效后再调一次
curl -s "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo" | head -c 400
echo
echo "SECRET=$SECRET"
