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


def render(c: dict, clients: list[dict], siblings: list[dict]) -> str:
    name = c["name"]
    slug = c["slug"]
    parts: list[str] = []

    parts.append(f"# {name} MCP server — through HeyMetra")
    parts.append("")
    parts.append(
        f"> **Unofficial.** This is not {name}'s own MCP server and this repository is not "
        f"affiliated with, endorsed by or supported by {name}. It documents how "
        f"[HeyMetra]({SITE}/), a remote MCP server built by Zeisoft, reads {name}."
    )
    parts.append("")
    if c.get("tagline"):
        parts.append(f"**{c['tagline'].rstrip('.')}.**")
        parts.append("")
    parts.append(
        f"[![MCP Registry](https://img.shields.io/badge/MCP_Registry-com.heymetra%2Fheymetra-1f6feb)]({REGISTRY})\n"
        f"[![Transport](https://img.shields.io/badge/transport-Streamable_HTTP-444)](https://modelcontextprotocol.io/)\n"
        f"[![Auth](https://img.shields.io/badge/auth-OAuth_2.1-444)]({SITE}/security/)\n"
        f"[![Connector page](https://img.shields.io/badge/heymetra.com-{slug}-1f6feb)]({SITE}/connectors/{slug}/)"
    )
    parts.append("")
    parts.append("---")
    parts.append("")

    if c.get("what"):
        parts.append(f"## What {name} is")
        parts.append("")
        parts.append(c["what"].strip())
        parts.append("")

    if c.get("how"):
        parts.append(f"## What HeyMetra reads from {name}")
        parts.append("")
        parts.append(c["how"].strip())
        parts.append("")

    if c.get("can_ask"):
        parts.append("## What you can ask")
        parts.append("")
        parts.append("Once connected, in your own assistant, in plain language:")
        parts.append("")
        for q in c["can_ask"]:
            parts.append(f"> {q}")
            parts.append("")

    table = permissions_table(c)
    if table:
        parts.append("## Permissions")
        parts.append("")
        parts.append(
            "You switch these on per connection, and a permission you leave off is a tool "
            "your assistant never sees."
        )
        parts.append("")
        parts.append(table)
        parts.append("")

    actions = c.get("actions") or []
    if actions:
        parts.append("## What it can change")
        parts.append("")
        for a in actions:
            parts.append(f"- {a}")
        parts.append("")
        # The write bounds only belong on a connector that can write. Printed under a
        # read-only source they describe budgets and campaigns it does not have, which
        # reads as boilerplate and teaches the reader to skip the section that matters
        # on the connectors where it is real.
        if any(
            o.get("writes")
            for perm in (c.get("consent") or {}).get("permissions") or []
            for o in perm.get("operations") or []
        ):
            # Name the bound that applies to THIS connector. A budget ceiling quoted
            # under a chat channel is as much noise as it was under a read-only source.
            bound = (
                "at most 20 messages a rolling day, counted separately from account changes"
                if c.get("kind") == "channel"
                else "±50% on a budget, 5 campaigns per action and 20 changes a rolling day"
            )
            parts.append(
                "A tool that would change something returns the change for a person to approve "
                "instead of running it, inside bounds that live in code rather than in a prompt: "
                f"{bound}, and an approval that expires after 30 minutes. "
                f"[How that works]({SITE}/security/)."
            )
            parts.append("")

    parts.append(f"## Connect {name}")
    parts.append("")
    parts.append(setup_section(c))
    parts.append("")

    parts.append("## Then add HeyMetra to your assistant")
    parts.append("")
    parts.append(client_block(clients))

    probs = problems_section(c)
    if probs:
        parts.append("## When something goes wrong")
        parts.append("")
        parts.append(probs)

    parts.append("## Everything else HeyMetra reads")
    parts.append("")
    parts.append(
        "One connection answers across accounts — which is the point, because spend lives in one "
        "place and revenue in another:"
    )
    parts.append("")
    by_cat: dict[str, list[str]] = {}
    for s in siblings:
        if s["slug"] == slug:
            link = f"**{s['name']}**"
        elif published(s):
            link = f"[{s['name']}](https://github.com/zeisoft/{repo_name(s['slug'])})"
        else:
            # No repository for it, so the link goes where the truth is kept.
            link = f"[{s['name']}]({SITE}/connectors/{s['slug']}/)"
        by_cat.setdefault(s["category"], []).append(link)
    for cat, items in by_cat.items():
        parts.append(f"**{cat}** — " + " · ".join(items))
        parts.append("")
    parts.append(
        f"The full catalogue, with what each one can do today, is at "
        f"[{SITE.replace('https://','')}/connectors/]({SITE}/connectors/)."
    )
    parts.append("")

    parts.append("## Links")
    parts.append("")
    parts.append(f"- [{name} connector page]({SITE}/connectors/{slug}/) — the source this page is generated from")
    parts.append(f"- [HeyMetra]({SITE}/) — what the product is")
    parts.append(f"- [Setup per assistant]({SITE}/mcp/) — eight clients, step by step")
    parts.append(f"- [Security and limits]({SITE}/security/)")
    parts.append(f"- [Pricing]({SITE}/pricing/) — paid, no free plan and no trial")
    parts.append("- [HeyMetra's own repository](https://github.com/zeisoft/heymetra-mcp)")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append(
        "<sub>This README is generated from HeyMetra's live connector catalogue and refreshed daily; "
        "it is committed only when something in it actually changed. Corrections are welcome as issues. "
        "Built by <a href=\"https://zeisoft.com\">Zeisoft</a>.</sub>"
    )
    parts.append("")
    return "\n".join(parts)


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
