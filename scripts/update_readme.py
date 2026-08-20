#!/usr/bin/env python3
"""Regenerate the auto-updated sections of the profile README.

Fetches the user's recently starred repositories and recently pushed
repositories from the GitHub API, then rewrites the content between the
<!-- STARS:START/END --> and <!-- REPOS:START/END --> markers in README.md.

Requires the GITHUB_TOKEN environment variable (provided automatically in
GitHub Actions). No third-party dependencies.
"""

import json
import os
import re
import sys
import urllib.request

USER = os.environ.get("GITHUB_USER", "UnknownObject777")
README = os.path.join(os.path.dirname(__file__), "..", "README.md")

STARS_LIMIT = 10
REPOS_LIMIT = 8


def gh_api(path, accept="application/vnd.github+json"):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": accept,
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "profile-readme-updater",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def esc(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def render_stars():
    items = gh_api(
        f"/users/{USER}/starred?per_page={STARS_LIMIT}",
        accept="application/vnd.github.star+json",
    )
    lines = [
        "| 项目 | 简介 | 语言 | Stars |",
        "| --- | --- | --- | --- |",
    ]
    for item in items:
        repo = item["repo"]
        desc = esc(repo.get("description")) or "-"
        lang = repo.get("language") or "-"
        lines.append(
            f"| [{repo['full_name']}]({repo['html_url']}) | {desc} "
            f"| {lang} | ⭐ {repo['stargazers_count']} |"
        )
    return "\n".join(lines)


def render_repos():
    repos = gh_api(f"/users/{USER}/repos?sort=pushed&per_page={REPOS_LIMIT}")
    lines = [
        "| 仓库 | 简介 | 语言 | 最近更新 |",
        "| --- | --- | --- | --- |",
    ]
    for repo in repos:
        desc = esc(repo.get("description")) or "-"
        lang = repo.get("language") or "-"
        pushed = repo["pushed_at"][:10]
        lines.append(
            f"| [{repo['name']}]({repo['html_url']}) | {desc} | {lang} | {pushed} |"
        )
    return "\n".join(lines)


def replace_block(content, tag, body):
    pattern = re.compile(
        rf"(<!-- {tag}:START -->\n).*?(<!-- {tag}:END -->)", re.DOTALL
    )
    if not pattern.search(content):
        sys.exit(f"error: marker {tag} not found in README.md")
    return pattern.sub(rf"\1{body}\n\2", content)


def main():
    with open(README, encoding="utf-8") as f:
        content = f.read()
    content = replace_block(content, "STARS", render_stars())
    content = replace_block(content, "REPOS", render_repos())
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("README.md updated.")


if __name__ == "__main__":
    main()
