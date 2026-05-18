#!/usr/bin/env python3
"""Sync GitHub milestone issues into the matching region's description.

For every region with a `milestone_ref` field, fetch all issues in that
milestone (open + closed) and replace the content between the
`<!-- AUTO_GH_ISSUES:START -->` and `<!-- AUTO_GH_ISSUES:END -->` markers
in both `desc.en` and `desc.zh`.

milestone_ref schema:
    "milestone_ref": {
        "repo": "ChronoAIProject/Ornn",
        "milestone": "M0 — Engineering Foundation & Infra"
    }

Usage:
    python3 tools/sync_milestone_issues.py            # update regions.json in place
    python3 tools/sync_milestone_issues.py --check    # exit 1 if any region would change (CI)
    python3 tools/sync_milestone_issues.py --region <key>  # sync just one region

Requires `gh` CLI authenticated with access to all referenced repos
(including private ones — needs a PAT/GH App in CI for cross-repo or private repo access).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REGIONS_FILE = REPO_ROOT / "regions.json"

AUTO_START = "<!-- AUTO_GH_ISSUES:START -->"
AUTO_END = "<!-- AUTO_GH_ISSUES:END -->"
AUTO_BLOCK_RE = re.compile(
    re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END),
    re.DOTALL,
)


def fetch_milestone_issues(repo: str, milestone_title: str) -> tuple[list, int | None]:
    """Return (issues, milestone_number). Issues sorted: open first, then closed, both by number desc."""
    ms_raw = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/milestones?state=all", "--paginate",
         "-q", ".[] | {number, title, state, description, html_url}"],
        text=True,
    )
    milestones = [json.loads(line) for line in ms_raw.strip().split("\n") if line.strip()]
    matched = next((m for m in milestones if m["title"] == milestone_title), None)
    if not matched:
        print(f"  WARN: milestone '{milestone_title}' not found in {repo}", file=sys.stderr)
        return [], None

    ms_num = matched["number"]
    issues_raw = subprocess.check_output(
        ["gh", "issue", "list", "--repo", repo,
         "--milestone", milestone_title, "--state", "all", "--limit", "500",
         "--json", "number,title,state,url"],
        text=True,
    )
    issues = json.loads(issues_raw)
    issues.sort(key=lambda i: (i["state"] != "OPEN", -i["number"]))
    return issues, ms_num


def format_block(repo: str, milestone_title: str, ms_num: int | None, issues: list, lang: str) -> str:
    """Render the auto-sync block content (between markers)."""
    if ms_num is None:
        return "_Milestone not found on GitHub — check `milestone_ref.milestone` value._"

    ms_url = f"https://github.com/{repo}/milestone/{ms_num}"
    open_n = sum(1 for i in issues if i["state"] == "OPEN")
    closed_n = sum(1 for i in issues if i["state"] == "CLOSED")

    if lang == "zh":
        header = (
            f"**GitHub issues** — [{milestone_title}]({ms_url}) · "
            f"{open_n} 进行中 / {closed_n} 已关闭"
        )
        open_label = "进行中"
        closed_label = "已关闭"
    else:
        header = (
            f"**GitHub issues** — [{milestone_title}]({ms_url}) · "
            f"{open_n} open / {closed_n} closed"
        )
        open_label = "Open"
        closed_label = "Closed"

    lines = [header, ""]
    open_issues = [i for i in issues if i["state"] == "OPEN"]
    closed_issues = [i for i in issues if i["state"] == "CLOSED"]

    if open_issues:
        lines.append(f"_{open_label}:_")
        for i in open_issues:
            t = i["title"].replace("|", "\\|")
            lines.append(f"- [#{i['number']}]({i['url']}) {t}")
        lines.append("")

    if closed_issues:
        lines.append(f"_{closed_label} (most recent first):_")
        # Cap closed at 25 to keep desc manageable; surface a "+N more" indicator
        cap = 25
        for i in closed_issues[:cap]:
            t = i["title"].replace("|", "\\|")
            lines.append(f"- [#{i['number']}]({i['url']}) ~~{t}~~")
        if len(closed_issues) > cap:
            lines.append(f"- _… and {len(closed_issues) - cap} more closed_")

    return "\n".join(lines)


def replace_block(text: str, new_inner: str) -> str:
    new_block = f"{AUTO_START}\n{new_inner}\n{AUTO_END}"
    if AUTO_BLOCK_RE.search(text):
        return AUTO_BLOCK_RE.sub(new_block, text)
    # No marker block — append one
    return text.rstrip() + "\n\n" + new_block


def sync_region(region: dict, key: str) -> bool:
    """Update region's desc in place. Return True if changed."""
    ref = region.get("milestone_ref")
    if not ref:
        return False
    repo = ref["repo"]
    title = ref["milestone"]
    issues, ms_num = fetch_milestone_issues(repo, title)

    changed = False
    for lang in ("en", "zh"):
        desc = region.get("desc", {}).get(lang, "")
        new_inner = format_block(repo, title, ms_num, issues, lang)
        new_desc = replace_block(desc, new_inner)
        if new_desc != desc:
            region.setdefault("desc", {})[lang] = new_desc
            changed = True

    # Update issue_count to actual open count
    if ms_num is not None:
        open_n = sum(1 for i in issues if i["state"] == "OPEN")
        if region.get("issue_count") != open_n:
            region["issue_count"] = open_n
            changed = True

    return changed


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true", help="exit 1 if anything would change")
    p.add_argument("--region", help="sync only this region key")
    args = p.parse_args()

    data = json.loads(REGIONS_FILE.read_text())
    regions = data["regions"]

    targets = [args.region] if args.region else [k for k, r in regions.items() if r.get("milestone_ref")]
    if not targets:
        print("no regions with milestone_ref found")
        return

    print(f"syncing {len(targets)} regions...")
    any_changed = False
    for key in targets:
        if key not in regions:
            print(f"  SKIP: {key} not in regions.json")
            continue
        changed = sync_region(regions[key], key)
        marker = "✓ changed" if changed else "  no-op "
        print(f"  {marker} {key}")
        any_changed = any_changed or changed

    if not any_changed:
        print("\nno changes")
        return

    if args.check:
        print("\nCHECK mode: regions.json is out of date")
        sys.exit(1)

    # Write back, preserving Unicode + 2-space indent (matches existing file style)
    REGIONS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("\nregions.json updated")


if __name__ == "__main__":
    main()
