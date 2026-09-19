# tools

`render.py` builds this repository's README from HeyMetra's live connector
catalogue (`https://api.heymetra.com/api/connectors`) — the same document the
marketing site builds from.

Run it by hand:

```bash
python3 tools/render.py zoho-salesiq --inplace
```

It refuses to write a README from a partial read of the catalogue, and it fails
if a tool identifier (`get_…`) reaches the output: those are precise about a
thing the reader has no reason to know, so the permission sentences are used
instead.
