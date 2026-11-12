#!/usr/bin/env python3
"""DataForSEO helper for the phonetic-obliterator skill (stdlib only).

For agents with no DataForSEO MCP tool. Reads credentials from the
environment variables DATAFORSEO_USERNAME and DATAFORSEO_PASSWORD (API login
and API password from https://app.dataforseo.com/api-access). Credentials are
never printed.

Subcommands
  check
      Free account lookup (GET /v3/appendix/user_data). Prints PASS and
      exits 0 only if the API returns status_code 20000; else prints FAIL
      with the reason and exits 1.

  volumes KEYWORD [KEYWORD ...] [--location-code 2840] [--language-code en]
      Search volume, difficulty, CPC and intent per keyword
      (POST /v3/dataforseo_labs/google/keyword_overview/live). Paid.

  suggestions SEED [--limit 20] [--location-code 2840] [--language-code en]
      Longer phrases that contain SEED, highest volume first
      (POST /v3/dataforseo_labs/google/keyword_suggestions/live). Paid.

Output is one compact JSON object per call. Exit codes: 0 ok, 1 API or
network error, 2 missing credentials or bad arguments.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.dataforseo.com"
TIMEOUT = 60


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def fail(msg, code=1):
    out({"ok": False, "error": msg})
    sys.exit(code)


def auth_header():
    user = os.environ.get("DATAFORSEO_USERNAME", "").strip()
    pwd = os.environ.get("DATAFORSEO_PASSWORD", "").strip()
    missing = [n for n, v in (("DATAFORSEO_USERNAME", user), ("DATAFORSEO_PASSWORD", pwd)) if not v]
    if missing:
        fail("Missing environment variable(s): " + ", ".join(missing)
             + ". Set them to your DataForSEO API login and API password"
             " (https://app.dataforseo.com/api-access), or run without keyword locks.", 2)
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return "Basic " + token


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", auth_header())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("status_message", "")
        except Exception:
            detail = ""
        hint = " (check the username and password)" if e.code == 401 else ""
        fail(f"HTTP {e.code} {e.reason}{hint}" + (f": {detail}" if detail else ""))
    except urllib.error.URLError as e:
        fail(f"Network error: {e.reason}")
    except (TimeoutError, OSError) as e:
        fail(f"Network error: {e}")
    except json.JSONDecodeError:
        fail("DataForSEO returned a response that isn't JSON.")


def first_task(resp):
    if resp.get("status_code") != 20000:
        fail(f"API status {resp.get('status_code')}: {resp.get('status_message')}")
    tasks = resp.get("tasks") or []
    if not tasks:
        fail("API returned no tasks.")
    t = tasks[0]
    if t.get("status_code") != 20000:
        fail(f"Task status {t.get('status_code')}: {t.get('status_message')}")
    return t


def row(item):
    info = item.get("keyword_info") or {}
    props = item.get("keyword_properties") or {}
    intent = (item.get("search_intent_info") or {}).get("main_intent")
    return {
        "keyword": item.get("keyword"),
        "volume": info.get("search_volume"),
        "difficulty": props.get("keyword_difficulty"),
        "cpc": info.get("cpc"),
        "intent": intent,
    }


def items_of(task):
    result = task.get("result") or []
    return (result[0].get("items") if result else None) or []


def cmd_check(_args):
    resp = call("GET", "/v3/appendix/user_data")
    if resp.get("status_code") == 20000:
        out({"ok": True, "check": "PASS", "status_code": 20000})
        return
    out({"ok": False, "check": "FAIL", "status_code": resp.get("status_code"),
         "status_message": resp.get("status_message")})
    sys.exit(1)


def cmd_volumes(args):
    kws = [k.strip() for k in args.keywords if k.strip()]
    if not kws:
        fail("Give at least one keyword.", 2)
    body = [{"keywords": kws, "location_code": args.location_code,
             "language_code": args.language_code}]
    t = first_task(call("POST", "/v3/dataforseo_labs/google/keyword_overview/live", body))
    rows = [row(i) for i in items_of(t)]
    found = {(r["keyword"] or "").lower() for r in rows}
    no_data = [k for k in kws if k.lower() not in found]
    out({"ok": True, "cost": t.get("cost"), "location_code": args.location_code,
         "language_code": args.language_code, "keywords": rows, "no_data": no_data})


def cmd_suggestions(args):
    body = [{"keyword": args.seed, "location_code": args.location_code,
             "language_code": args.language_code, "limit": args.limit,
             "order_by": ["keyword_info.search_volume,desc"]}]
    t = first_task(call("POST", "/v3/dataforseo_labs/google/keyword_suggestions/live", body))
    out({"ok": True, "cost": t.get("cost"), "seed": args.seed,
         "location_code": args.location_code, "language_code": args.language_code,
         "keywords": [row(i) for i in items_of(t)]})


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    except (AttributeError, ValueError):
        pass
    ap =argparse.ArgumentParser(description="DataForSEO helper (env vars DATAFORSEO_USERNAME / DATAFORSEO_PASSWORD).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="free account check; PASS only on status_code 20000")

    def geo(p):
        p.add_argument("--location-code", type=int, default=2840, help="default 2840 (United States)")
        p.add_argument("--language-code", default="en", help="default en")

    v = sub.add_parser("volumes", help="search volume and difficulty per keyword")
    v.add_argument("keywords", nargs="+")
    geo(v)

    s = sub.add_parser("suggestions", help="longer phrases containing a seed keyword")
    s.add_argument("seed")
    s.add_argument("--limit", type=int, default=20)
    geo(s)

    args = ap.parse_args()
    {"check": cmd_check, "volumes": cmd_volumes, "suggestions": cmd_suggestions}[args.cmd](args)


if __name__ == "__main__":
    main()
