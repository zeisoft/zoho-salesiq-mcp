#!/usr/bin/env python3
"""Render one connector's README from the live HeyMetra catalogue.

Everything printed here comes from https://api.heymetra.com/api/connectors, which
is the same document the marketing site builds from. Nothing about a connector is
written by hand, so a connector that gains a capability gains a section without
anyone editing anything.

Two rules are load-bearing and both are enforced below rather than remembered:

**No tool identifiers.** The consent contract carries `operations[].tool`
(`get_orders`) beside `operations[].label` (a sentence). The owner's ruling on
ZEISO-385: "get_orders gibi tool tanımlarına gerek yok, kullanıcı için bir şey
ifade etmiyor." Only labels are rendered, and `assert_no_tool_names` fails the
render if an identifier reaches the output by any other route.

**A connector that cannot be connected does not get a setup guide.** `soon`
connectors have no `setup_guide` in the catalogue, and inventing one would
publish instructions for something nobody can do. They get a stated absence
instead — which flips to the real guide on the day the catalogue changes,
because this runs daily.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request

CATALOG_URL = "https://api.heymetra.com/api/connectors"
SITE = "https://heymetra.com"
ENDPOINT = "https://mcp.heymetra.com/mcp"
REGISTRY = "https://registry.modelcontextprotocol.io/v0/servers/com.heymetra%2Fheymetra/versions"

# Connectors that get no repository of their own. Email is delivery with nothing
# provider-shaped to document — the owner's call, 2026-09-19.
EXCLUDED = {"email"}


def published(c: dict) -> bool:
    """Whether this connector gets a repository.

    Only what a customer can connect today. A `soon` connector has no setup guide
    in the catalogue, and a repository whose setup section says "not yet" is a
    page that breaks its promise at the first click — the owner's call, 2026-09-19.

    Consequence worth knowing: when a `soon` connector goes live, its repository
    does not appear by itself. The daily workflow keeps existing repositories
    true; creating a new one is a run of this script.
    """
    return c["slug"] not in EXCLUDED and c.get("availability") == "available"


def fetch_catalog() -> dict:
    req = urllib.request.Request(CATALOG_URL, headers={"User-Agent": "heymetra-docs-generator"})
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status != 200:
            raise SystemExit(f"catalogue returned {r.status}; refusing to render from a partial read")
        data = json.load(r)
    if not data.get("connectors") or not data.get("mcp_clients"):
        raise SystemExit("catalogue answered without connectors or clients; refusing to render")
    return data


def repo_name(slug: str) -> str:
    return f"{slug}-mcp"


def client_block(clients: list[dict]) -> str:
    """The setup section every repository shares, built from the catalogue's own
    client facts — including which key holds the URL, which Antigravity spells
    differently from everyone else."""
    out = [
        "Add HeyMetra once and it is there in every conversation. The address is the same everywhere:",
        "",
        "```",
        ENDPOINT,
        "```",
        "",
    ]
    for c in clients:
        s = c.get("setup") or {}
        where, kind, key, note = s.get("where", ""), s.get("kind"), s.get("url_key"), s.get("note")
        out.append("<details>")
        out.append(f"<summary><b>{c['name']}</b> — {where}</summary>")
        out.append("")
        if kind == "command":
            out.append("```bash")
            out.append(f"{where} heymetra {ENDPOINT}")
            out.append("```")
        elif kind == "file" and key:
            if where.endswith(".toml") or ".toml" in where:
                out.append("```toml")
                out.append("[mcp_servers.heymetra]")
                out.append(f'url = "{ENDPOINT}"')
                out.append("```")
            else:
                out.append("```json")
                out.append("{")
                out.append('  "mcpServers": {')
                out.append(f'    "heymetra": {{ "{key}": "{ENDPOINT}" }}')
                out.append("  }")
                out.append("}")
                out.append("```")
        else:
            out.append(f"Paste the address above into {where}.")
        if note:
            out.append("")
            out.append(f"_{note[0].upper()}{note[1:]}._")
        out.append("")
        out.append(f"Full walkthrough: [{SITE.replace('https://', '')}/mcp/{c['slug']}/]({SITE}/mcp/{c['slug']}/)")
        out.append("</details>")
        out.append("")
    return "\n".join(out)


def permissions_table(c: dict) -> str:
    """What the connector may do, grouped the way the customer switches it.

    Labels only. `writes` decides whether the row says a change is proposed —
    which is the one thing a reader of a connector's page actually needs from the
    operation list.
    """
    perms = (c.get("consent") or {}).get("permissions") or []
    if not perms:
        return ""
    rows = ["| Permission | What it covers | Changes anything? |", "|---|---|---|"]
    for p in perms:
        ops = p.get("operations") or []
        writes = any(o.get("writes") for o in ops)
        limits = p.get("limits") or []
        desc = p.get("description", "").rstrip(".")
        if limits:
            desc += " — " + "; ".join(str(x) for x in limits)
        rows.append(
            f"| **{p.get('label', p.get('key'))}** | {desc}. | "
            f"{'Yes — every change waits for your approval' if writes else 'No, read only'} |"
        )
    body = "\n".join(rows)

    detail = []
    for p in perms:
        for o in p.get("operations") or []:
            line = o.get("label", "").strip()
            if line and line not in detail:
                detail.append(line)
    if detail:
        body += "\n\n<details>\n<summary>What each permission lets an assistant do, in full</summary>\n\n"
        body += "\n".join(f"- {d}" for d in detail)
        body += "\n</details>"
    return body


def setup_section(c: dict) -> str:
    name = c["name"]
    guide = c.get("setup_guide") or {}
    steps = guide.get("steps") or []
    fields = c.get("credential_fields") or []

    if c.get("availability") != "available":
        out = [
            f"**{name} is not connectable in HeyMetra yet.** The catalogue lists it as *coming soon*, "
            f"and this page will carry the steps on the day that changes — it is generated from the "
            f"catalogue daily, so it cannot promise a flow that does not exist.",
            "",
            f"[Follow the connector page]({SITE}/connectors/{c['slug']}/) for the current state.",
        ]
        return "\n".join(out)

    out = []
    if steps:
        for i, s in enumerate(steps, 1):
            out.append(f"**{i}. {s.get('title','').strip()}**")
            out.append("")
            if s.get("detail"):
                out.append(s["detail"].strip())
                out.append("")
            if s.get("tip"):
                out.append(f"> {s['tip'].strip()}")
                out.append("")
    elif c.get("connect_steps"):
        for i, s in enumerate(c["connect_steps"], 1):
            out.append(f"{i}. {s}")
        out.append("")
    else:
        method = {"api_key": "an API key", "oauth": "an OAuth sign-in", "builtin": "no credential"}.get(
            c.get("connect_method", ""), "a credential"
        )
        out.append(f"{name} connects with {method}. The steps are on the "
                   f"[connector page]({SITE}/connectors/{c['slug']}/).")
        out.append("")

    rejects = [r for f in fields for r in (f.get("rejects") or [])]
    if rejects:
        out.append("Watch what you paste:")
        out.append("")
        for r in rejects:
            out.append(f"- Anything starting `{r['prefix']}` is **{r['what']}** and will be refused by name.")
        out.append("")
    return "\n".join(out).rstrip()


def problems_section(c: dict) -> str:
    problems = (c.get("setup_guide") or {}).get("problems") or []
    if not problems:
        return ""
    out = []
    for p in problems:
        out.append(f"<details>\n<summary>{p.get('symptom','').strip()}</summary>\n")
        if p.get("cause"):
            out.append(f"**Why:** {p['cause'].strip()}\n")
        if p.get("fix"):
            out.append(f"**Fix:** {p['fix'].strip()}\n")
        out.append("</details>\n")
    return "\n".join(out)


HOOKS = {
    "Mobile": "Your subscription revenue lives in {name}. What you paid to get those "
              "subscribers does not. Ask about both in the same sentence.",
    "Ecommerce": "Your orders live in {name}. What you spent to win them lives in your ad "
                 "accounts. One question, both answers.",
    "Analytics": "{name} knows what people did. It does not know what it cost, or what it "
                 "earned. Connect it beside the accounts that do.",
    "Revenue & CRM": "Your pipeline lives in {name}. What it cost to fill it lives somewhere "
                     "else entirely. Ask once, across both.",
    "Ads": "{name} tells you what you spent. It cannot tell you what came back. Put it beside "
           "the accounts that hold the revenue.",
    "Channels": "An answer nobody reads is not an answer. Have it delivered to {name}, where "
                "the team already is.",
}


def hook(c: dict) -> str:
    """The opening line.

    A connector page that opens by defining the provider is writing for someone who
    has not heard of a product they already pay for. The definition still earns its
    place further down, where it reads as reference rather than as a greeting.
    """
    template = HOOKS.get(c["category"], "Connect {name} once, then ask about it in plain language.")
    return template.format(name=c["name"])


def render(c: dict, clients: list[dict], siblings: list[dict]) -> str:
    name = c["name"]
    slug = c["slug"]
    p: list[str] = []

    p.append('<div align="center">')
    p.append("")
    p.append(f'<img src="assets/cover.png" alt="{name} through HeyMetra\'s MCP server" width="100%">')
    p.append("")
    p.append(f"# {name} &times; HeyMetra")
    p.append("")
    if c.get("tagline"):
        p.append(f"**{c['tagline'].strip().rstrip('.')}.**")
        p.append("")
    p.append(hook(c))
    p.append("")
    p.append(
        f"[![MCP Registry](https://img.shields.io/badge/MCP_Registry-com.heymetra%2Fheymetra-1f6feb)]({REGISTRY})\n"
        f"[![Transport](https://img.shields.io/badge/transport-Streamable_HTTP-444)](https://modelcontextprotocol.io/)\n"
        f"[![Auth](https://img.shields.io/badge/auth-OAuth_2.1-444)]({SITE}/security/)\n"
        f"[![Connector page](https://img.shields.io/badge/heymetra.com-{slug}-1f6feb)]({SITE}/connectors/{slug}/)"
    )
    p.append("")
    p.append("```")
    p.append(ENDPOINT)
    p.append("```")
    p.append("")
    p.append("</div>")
    p.append("")
    p.append("---")
    p.append("")

    if c.get("can_ask"):
        p.append("## Ask it things like")
        p.append("")
        for q in c["can_ask"]:
            p.append(f"> {q}")
            p.append("")
        p.append(
            "No dashboard, no export, no query language. You ask in the assistant you already "
            "use and the answer comes back with the account it came from."
        )
        p.append("")

    p.append(f"## Connect {name}")
    p.append("")
    p.append(setup_section(c))
    p.append("")

    p.append("## Then add HeyMetra to your assistant")
    p.append("")
    p.append(client_block(clients))

    table = permissions_table(c)
    actions = c.get("actions") or []
    if table or actions:
        p.append("## What it may and may not touch")
        p.append("")
        for a in actions:
            p.append(f"{a}")
            p.append("")
        if table:
            p.append(
                "Permissions are switched on per connection, and one you leave off is a tool "
                "your assistant never sees."
            )
            p.append("")
            p.append(table)
            p.append("")
        if any(
            o.get("writes")
            for perm in (c.get("consent") or {}).get("permissions") or []
            for o in perm.get("operations") or []
        ):
            bound = (
                "at most 20 messages a rolling day, counted separately from account changes"
                if c.get("kind") == "channel"
                else "±50% on a budget, 5 campaigns per action and 20 changes a rolling day"
            )
            p.append(
                "Anything that would change something comes back as a proposal you approve, "
                f"inside bounds that live in code rather than in a prompt: {bound}, and an "
                f"approval that expires after 30 minutes. [How that works]({SITE}/security/)."
            )
            p.append("")

    probs = problems_section(c)
    if probs:
        p.append("## When something goes wrong")
        p.append("")
        p.append(probs)

    if c.get("how"):
        p.append(f"## What HeyMetra reads from {name}")
        p.append("")
        p.append(c["how"].strip())
        p.append("")

    if c.get("what"):
        p.append("<details>")
        p.append(f"<summary>About {name}</summary>")
        p.append("")
        p.append(c["what"].strip())
        p.append("</details>")
        p.append("")

    p.append("## One connection, not seven")
    p.append("")
    p.append(
        "The reason to read {n} through HeyMetra rather than through a server that only knows "
        "{n} is everything else it can answer in the same breath:".format(n=name)
    )
    p.append("")
    by_cat: dict[str, list[str]] = {}
    for s in siblings:
        if s["slug"] == slug:
            link = f"**{s['name']}**"
        elif published(s):
            link = f"[{s['name']}](https://github.com/zeisoft/{repo_name(s['slug'])})"
        else:
            link = f"[{s['name']}]({SITE}/connectors/{s['slug']}/)"
        by_cat.setdefault(s["category"], []).append(link)
    for cat, items in by_cat.items():
        p.append(f"**{cat}** — " + " · ".join(items))
        p.append("")
    p.append(f"The full catalogue is at [{SITE.replace('https://','')}/connectors/]({SITE}/connectors/).")
    p.append("")

    p.append("## Links")
    p.append("")
    p.append(f"- [{name} connector page]({SITE}/connectors/{slug}/)")
    p.append(f"- [HeyMetra]({SITE}/) — what the product is")
    p.append(f"- [Setup for every assistant]({SITE}/mcp/)")
    p.append(f"- [Security and limits]({SITE}/security/)")
    p.append(f"- [Pricing]({SITE}/pricing/)")
    p.append("- [HeyMetra's own repository](https://github.com/zeisoft/heymetra-mcp)")
    p.append("")
    p.append("---")
    p.append("")
    p.append(
        f"<sub>Built by <a href=\"https://zeisoft.com\">Zeisoft</a>, who make HeyMetra. "
        f"Not affiliated with {name}. This README is generated from HeyMetra's live connector "
        f"catalogue and refreshed daily; corrections are welcome as issues.</sub>"
    )
    p.append("")
    return "\n".join(p)


TOOL_NAME = re.compile(r"\b(get|list|create|update|pause|rename|approve|reject|undo|submit|send)_[a-z_]{3,}\b")


def assert_no_tool_names(text: str, slug: str) -> None:
    """ZEISO-385: identifiers are precise about a thing the reader has no reason to know."""
    hits = {m.group(0) for m in TOOL_NAME.finditer(text)}
    if hits:
        raise SystemExit(f"{slug}: tool identifiers reached the output: {sorted(hits)}")


def main() -> None:
    catalog = fetch_catalog()
    clients = catalog["mcp_clients"]
    siblings = [c for c in catalog["connectors"] if c["slug"] not in EXCLUDED]
    wanted = [c for c in siblings if published(c)]
    only = sys.argv[1] if len(sys.argv) > 1 else None
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    for c in wanted:
        if only and c["slug"] != only:
            continue
        text = render(c, clients, siblings)
        assert_no_tool_names(text, c["slug"])
        # `--inplace` is how the daily workflow inside a connector's own repository
        # calls this: one slug, README.md beside it, nothing else touched.
        import os

        if out_dir == "--inplace":
            path = "README.md"
        else:
            path = f"{out_dir}/{repo_name(c['slug'])}/README.md"
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        print(f"{repo_name(c['slug']):32} {len(text):6} bytes  {c['availability']}")


if __name__ == "__main__":
    main()
