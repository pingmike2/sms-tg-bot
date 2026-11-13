# sms-tg-bot — 聚合免费接码站点的 Telegram 机器人（Cloudflare Workers）

一个跑在 Cloudflare Workers 上的单人 Telegram 机器人，把导航站 Free SMS 分区里的
免费接码站点聚合成一个入口：点站点 → 选号码 → 直接看验证码，不用在十几个网站之间来回跳。
默认只允许一个 Telegram 账号使用。

## 一键安装

```bash
git clone https://github.com/pingmike2/sms-tg-bot.git
cd sms-tg-bot
export CLOUDFLARE_API_TOKEN='你的cf token'
export CLOUDFLARE_ACCOUNT_ID='你的account id'
export BOT_TOKEN='123456:ABC...'        # @BotFather 拿
export OWNER_ID='你的telegram_user_id'   # @userinfobot 查
npx wrangler@latest deploy
bash deploy.sh                          # 写 secret + 注册 webhook
```

部署完成后给机器人发 `/start`。

## 架构

```
Telegram  ──webhook──▶  Worker (src/worker.js)
                          │
                          ├─ 鉴权：路径含 BOT_TOKEN + secret_token 头，缺一 403
                          ├─ 白名单：from.id !== OWNER_ID → 拒（私有机器人）
                          │
                          ▼
                    ADAPTERS[site].list()  ──▶ 号码列表（带最近短信时间，按活跃度排序）
                    ADAPTERS[site].read()  ──▶ 短信正文 + 解出的验证码
                          │
                          ▼
                   各接码站点（直连 HTTP，无浏览器）
```

Worker 内缓存 45~60 秒，避免重复打站。免费版 50 subrequest 上限是硬约束：
列表页只抓 1 次，读码时才多抓 1~2 次，不在列表阶段逐号抓落地页。

## 配置

| 变量 | 必填 | 说明 |
|---|---|---|
| `BOT_TOKEN` | 是 | Telegram bot token，`wrangler secret put BOT_TOKEN` 写入 |
| `OWNER_ID` | 是 | 唯一允许使用的 Telegram user id |
| `WEBHOOK_SECRET` | 建议 | 与 `setWebhook` 的 `secret_token` 一致，校验 `x-telegram-bot-api-secret-token` |
| `UPSTREAM` | 否 | `wrangler.toml` 里的普通变量，默认 `https://tempsmss.com` |

密钥全部走 `wrangler secret`，不落在仓库里。

### 支持状态

| 站点 | 列表 | 读码 | 说明 |
|---|---|---|---|
| `tempsmss` | ✅ | ✅ | 全解密，验证码直出 |
| `tiger-sms` | ✅ | ✅ | 带 Active 徽章与 Last SMS 时间 |
| `freereceivesms` | ✅ | ✅ | 完整国际号码 |
| `supercloudsms` | ✅ | ✅ | |
| `mianfeijiema` | ✅ | ✅ | 18 个号，验证码带 `data-clipboard-text` 明文，15/15 解出 |
| `receive-sms.cc` | ✅ | ✅ | 24 个号，`div.con` 明文，如 `Account: 786132` / `Verification code: 6914` |
| `sms-receive.net` | ✅ | ⚠️ | 列表 85 个号，但读码接口对现有号码全返 `[]` |
| 其余 22 个 | — | — | CF 拦截 / 需登录 / 纯 JS 渲染 / 需注册，按钮里不出现 |

站点清单来自导航站 Tools → Free SMS 分区，共 30 个，其中 8 个可直接用；不可用的也保留在
「全部站点状态」里并注明原因，方便日后上游恢复时快速接回。

### tempsmss 验证码解密

静态页面 HTML 里的验证码本身是 `••••••`（不是前端遮挡），真码只在
`POST https://tempsmss.com/wp-admin/admin-ajax.php` 的
`sms_receiver_get_messages` 响应里，以 `<span class="sms-spoiler" data-c="...">`
存放，`data-c` 为 base64。

`read()` 做的事：

1. 抓号码页，取 `data-post`（post_id）与 `security`（nonce）
2. POST 上面那个接口，拿到含明文的 HTML
3. 把所有 `sms-spoiler` 的 `data-c` 做 base64 解码
4. 正文里还残留 `•` 就标记解密失败，宁可不显示也不送假数据

验证码识别支持纯数字 4~8 位，也支持 `732-344` 这类分段格式（WhatsApp 用）。

## 快速参考（运维）

```bash
# 看实时日志
npx wrangler@latest tail tempsms-tg-bot

# 重新部署
npx wrangler@latest deploy

# 重设 webhook（改了 secret 后要重跑）
curl -s "https://tempsms-tg-bot.<你的子域>.workers.dev/setup"

# 健康检查（返回站点数与适配器数）
curl -s "https://tempsms-tg-bot.<你的子域>.workers.dev/health"
```

### 机器人不回复怎么办

先 `wrangler tail` 看有没有异常。最常见原因是**免费版 50 subrequest 上限**被撑爆，
表现是日志无异常但消息不发出去 —— 检查是不是在列表阶段就逐号抓了落地页。

### 验证码显示成 •••••• 怎么办

说明 ajax 接口那条路没通（nonce 过期或站点改版）。直接抓页面看 `sms-spoiler` 是否还在，
`data-c` 是不是 base64。若站点改成别的编码，`read()` 里的 `atob` 要跟着换。

## 注意事项

- **只给一个人用**：`OWNER_ID` 之外的用户会被直接拒绝，这是设计而非缺陷。
- **免费版 50 subrequest 上限**是硬约束，新增适配器时别在 `list()` 里逐号发请求。
- 部分站点用 TLS 指纹拦截（如 `sms-online.co`：`curl` 200 但 `node fetch` / Workers 403），
  这类站点纯 HTTP 绕不过去，已在清单里标为不可用，不做假数据兜底。
- 号码是公共号，验证码可能被别人读到；同一个号可能被要求 KYC（要姓名/邮箱），换号即可。
- 站点改版会导致解析失效，`test/parse.test.js` 与 `test/probe_all.py` 可用来快速复测。
- 本 Worker 不收集、不存储任何用户数据；缓存只在 Worker 内存里，随 isolate 回收。

## 致谢 (Acknowledgements)

| 项目 | 在本项目里干什么活 |
|---|---|
| [Cloudflare Workers](https://workers.cloudflare.com/) | 运行环境与 webhook 入口 |
| [Telegram Bot API](https://core.telegram.org/bots/api) | 机器人消息与回调按钮 |
| [wrangler](https://github.com/cloudflare/workers-sdk) | 部署与 secret 管理 |
| [nav.eooce.com](https://nav.eooce.com/) | Free SMS 站点清单来源 |

## 免责声明 (Disclaimer)

本项目仅供学习、研究与个人技术实验使用，请勿用于违反所访问站点服务条款或当地法律的行为。

与上述任何接码站点、Telegram、Cloudflare 均无关联、无背书（not affiliated or endorsed）。

各站点可用性完全取决于对方策略（改版、加墙、限流、下线），本项目不担保持续可用或稳定。

如果需要稳定的验证码接收通道，请使用正规付费短信服务的官方套餐。

使用产生的一切风险由使用者自行承担；软件本体按 LICENSE 提供，AS IS。

## License

[MIT](./LICENSE) © 2026 [pingmike2](https://github.com/pingmike2)
