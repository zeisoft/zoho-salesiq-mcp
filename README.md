<div align="center">

<img src="assets/cover.png" alt="Zoho SalesIQ through HeyMetra's MCP server" width="100%">

# Zoho SalesIQ &times; HeyMetra

**Live chat volume, and how much of it went unanswered.**

Your pipeline lives in Zoho SalesIQ. What it cost to fill it lives somewhere else entirely. Ask once, across both.

[![MCP Registry](https://img.shields.io/badge/MCP_Registry-com.heymetra%2Fheymetra-1f6feb)](https://registry.modelcontextprotocol.io/v0/servers/com.heymetra%2Fheymetra/versions)
[![Transport](https://img.shields.io/badge/transport-Streamable_HTTP-444)](https://modelcontextprotocol.io/)
[![Auth](https://img.shields.io/badge/auth-OAuth_2.1-444)](https://heymetra.com/security/)
[![Connector page](https://img.shields.io/badge/heymetra.com-zoho-salesiq-1f6feb)](https://heymetra.com/connectors/zoho-salesiq/)

```
https://mcp.heymetra.com/mcp
```

</div>

---

## Ask it things like

> How many chats came in last week, and how many did nobody answer?

> Which department took the most chats this month?

> Which days of the week are busiest on live chat?

No dashboard, no export, no query language. You ask in the assistant you already use and the answer comes back with the account it came from.

## Connect Zoho SalesIQ

**1. Connect it separately from Zoho CRM**

Choose Zoho SalesIQ on the Connections screen even if Zoho CRM is already connected. They are different products behind one sign-in, and a grant on one carries nothing to the other.

**2. Sign in as somebody who can see the chats**

On Zoho's own screen. SalesIQ scopes what an operator sees by department, so the account you use decides which conversations HeyMetra can count.

> An operator attached to one department produces figures for that department, which reads as a quiet site rather than as a narrow view.

**3. Grant the two read permissions**

Portals and conversations, both READ. Nothing about your CRM, and nothing that can send a chat message or reply to one.

**4. Pick the portal**

SalesIQ calls a site a portal, and an account can hold several. One HeyMetra connection is one portal; connect again to add another.

> The portal's screen name is part of every address HeyMetra calls, which is why it is chosen here rather than guessed later.

**5. Add HeyMetra to the assistant you use**

Claude, ChatGPT, Cursor or Codex. The chat tool appears there and answers from the live portal.

## Then add HeyMetra to your assistant

Add HeyMetra once and it is there in every conversation. The address is the same everywhere:

```
https://mcp.heymetra.com/mcp
```

### One command

```bash
npx add-mcp https://mcp.heymetra.com/mcp
```

[`add-mcp`](https://www.npmjs.com/package/add-mcp) is a third-party installer that writes the configuration for Claude Code, Codex, Cursor, Antigravity, VS Code and seventeen other agents. It infers the name from the address, so the server lands as `heymetra`. Run against this endpoint before it was written here.

### Or by hand

<details>
<summary><b>Claude</b> — Settings → Customize → Connectors → Add custom connector</summary>

Paste the address above into Settings → Customize → Connectors → Add custom connector.

_On Team and Enterprise plans only an owner can add it, under Organization settings._

Full walkthrough: [heymetra.com/mcp/claude/](https://heymetra.com/mcp/claude/)
</details>

<details>
<summary><b>ChatGPT</b> — Settings → Security and login → Developer mode, then chatgpt.com/plugins</summary>

Paste the address above into Settings → Security and login → Developer mode, then chatgpt.com/plugins.

_The endpoint has to include its /mcp path here._

Full walkthrough: [heymetra.com/mcp/chatgpt/](https://heymetra.com/mcp/chatgpt/)
</details>

<details>
<summary><b>Grok</b> — grok.com/connectors → New Connector → Custom</summary>

Paste the address above into grok.com/connectors → New Connector → Custom.

_XAI calls this “bring your own MCP”._

Full walkthrough: [heymetra.com/mcp/grok/](https://heymetra.com/mcp/grok/)
</details>

<details>
<summary><b>Perplexity</b> — Settings → Connectors → Custom connector → Remote</summary>

Paste the address above into Settings → Connectors → Custom connector → Remote.

_Perplexity documents it as a Pro, Max and Enterprise feature._

Full walkthrough: [heymetra.com/mcp/perplexity/](https://heymetra.com/mcp/perplexity/)
</details>

<details>
<summary><b>Claude Code</b> — claude mcp add --transport http</summary>

```bash
claude mcp add --transport http heymetra https://mcp.heymetra.com/mcp
```

_Or a .mcp.json in the project root; /mcp inside a session shows what connected._

Full walkthrough: [heymetra.com/mcp/claude-code/](https://heymetra.com/mcp/claude-code/)
</details>

<details>
<summary><b>Codex</b> — ~/.codex/config.toml</summary>

```toml
[mcp_servers.heymetra]
url = "https://mcp.heymetra.com/mcp"
```

_Under an [mcp_servers.<name>] section, then codex mcp login._

Full walkthrough: [heymetra.com/mcp/codex/](https://heymetra.com/mcp/codex/)
</details>

<details>
<summary><b>Cursor</b> — ~/.cursor/mcp.json, or .cursor/mcp.json in a project</summary>

```json
{
  "mcpServers": {
    "heymetra": { "url": "https://mcp.heymetra.com/mcp" }
  }
}
```

_Leave the static OAuth fields empty — they exist for servers that cannot register themselves._

Full walkthrough: [heymetra.com/mcp/cursor/](https://heymetra.com/mcp/cursor/)
</details>

<details>
<summary><b>Antigravity</b> — ~/.gemini/config/mcp_config.json, or .agents/mcp_config.json in a project</summary>

```json
{
  "mcpServers": {
    "heymetra": { "serverUrl": "https://mcp.heymetra.com/mcp" }
  }
}
```

_The key is serverUrl, not url — the one every other JSON client spells differently._

Full walkthrough: [heymetra.com/mcp/antigravity/](https://heymetra.com/mcp/antigravity/)
</details>

## What it may and may not touch

Propose a change through this account's own API, for operations HeyMetra does not cover. Nothing is sent until you approve it, and HeyMetra cannot undo it afterwards.

Permissions are switched on per connection, and one you leave off is a tool your assistant never sees.

| Permission | What it covers | Changes anything? |
|---|---|---|
| **Included with the connection** | What HeyMetra needs to set the connection up and nothing more. It cannot be switched off on its own — removing the connection is how you withdraw it. | No, read only |
| **Direct API access** | Let your assistant use this account's own API for anything HeyMetra's other operations do not cover. It reads directly, and what comes back is the provider's own answer rather than a figure HeyMetra has checked. It can also propose changes — those are never applied until you approve them, and HeyMetra cannot undo one afterwards. | Yes — every change waits for your approval |

<details>
<summary>What each permission lets an assistant do, in full</summary>

- Ask this account's own API a question HeyMetra's other operations do not cover. Reads only, and the answer is the provider's own rather than a figure HeyMetra has checked.
- Propose a change through this account's own API, for operations HeyMetra does not cover. Nothing is sent until you approve it, and HeyMetra cannot undo it afterwards.
</details>

Anything that would change something comes back as a proposal you approve, inside bounds that live in code rather than in a prompt: ±50% on a budget, 5 campaigns per action and 20 changes a rolling day, and an approval that expires after 30 minutes. [How that works](https://heymetra.com/security/).

## When something goes wrong

<details>
<summary>The chat figures are far lower than the SalesIQ dashboard shows.</summary>

**Why:** The account that authorised it is attached to one department rather than all of them, so it can only see that department's conversations.

**Fix:** Reconnect as an administrator, or as an operator attached to every department you want counted.

</details>

<details>
<summary>Another site's chats are missing.</summary>

**Why:** A connection carries one portal, and that site is a different portal.

**Fix:** Connect SalesIQ again and pick the other portal. Each connection is asked about by name.

</details>

## What HeyMetra reads from Zoho SalesIQ

SalesIQ needs its own sign-in, separate from Zoho CRM: connecting one asks for nothing from the other. Your MCP client gets one tool that reads the conversations — how many were started in a period, and how they split by status (the ones nobody picked up included), by department, by the operator who took them, by brand, or by day. A missed chat is a lead that leaves no record in the CRM at all, which is the question this connector exists for. The grant is SalesIQ's own conversations scope, so a conversation comes back as SalesIQ holds it: where SalesIQ captured a visitor's name, email or phone number, or what they typed, that is in the reply. It is what makes a chat matchable to a lead in your CRM, and it is why this connection should be treated as customer data rather than as a counter. Zoho can separate reading from writing, so you choose which at connect time; a read-only connection holds no permission to send a chat message to anybody.

<details>
<summary>About Zoho SalesIQ</summary>

Zoho SalesIQ is the live chat and visitor tracking on your website. It is where somebody who is not yet a lead asks their first question.
</details>

## One connection, not seven

The reason to read Zoho SalesIQ through HeyMetra rather than through a server that only knows Zoho SalesIQ is everything else it can answer in the same breath:

**Ads** — [Google Ads](https://heymetra.com/connectors/google-ads/) · [Meta](https://heymetra.com/connectors/meta-ads/)

**Analytics** — [Google Analytics 4](https://heymetra.com/connectors/google-analytics-4/) · [Google Search Console](https://github.com/zeisoft/google-search-console-mcp) · [PostHog](https://github.com/zeisoft/posthog-mcp)

**Ecommerce** — [Shopify](https://heymetra.com/connectors/shopify/) · [Trendyol](https://github.com/zeisoft/trendyol-mcp) · [WooCommerce](https://github.com/zeisoft/woocommerce-mcp)

**Revenue & CRM** — [Stripe](https://heymetra.com/connectors/stripe/) · [HubSpot](https://heymetra.com/connectors/hubspot/) · [Zoho CRM](https://github.com/zeisoft/zoho-crm-mcp) · **Zoho SalesIQ** · [Zoho Marketing Automation](https://github.com/zeisoft/zoho-marketing-automation-mcp)

**Mobile** — [AppsFlyer](https://github.com/zeisoft/appsflyer-mcp) · [RevenueCat](https://heymetra.com/connectors/revenuecat/) · [Adapty](https://github.com/zeisoft/adapty-mcp) · [App Store Connect](https://github.com/zeisoft/app-store-connect-mcp)

**Work** — [Google Calendar](https://heymetra.com/connectors/google-calendar/) · [Google Meet](https://heymetra.com/connectors/google-meet/) · [Jira](https://github.com/zeisoft/jira-mcp)

**Channels** — [Slack](https://github.com/zeisoft/slack-mcp) · [Telegram](https://github.com/zeisoft/telegram-mcp)

The full catalogue is at [heymetra.com/connectors/](https://heymetra.com/connectors/).

## Links

- [Zoho SalesIQ connector page](https://heymetra.com/connectors/zoho-salesiq/)
- [HeyMetra](https://heymetra.com/) — what the product is
- [Setup for every assistant](https://heymetra.com/mcp/)
- [Security and limits](https://heymetra.com/security/)
- [Pricing](https://heymetra.com/pricing/)
- [HeyMetra's own repository](https://github.com/zeisoft/heymetra-mcp)

---

<sub>Built by <a href="https://zeisoft.com">Zeisoft</a>, who make HeyMetra. Not affiliated with Zoho SalesIQ. This README is generated from HeyMetra's live connector catalogue and refreshed daily; corrections are welcome as issues.</sub>
