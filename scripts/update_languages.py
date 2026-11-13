#!/usr/bin/env python3
"""Hitung 3 bahasa teratas dari SEMUA repo (termasuk private) lalu tulis assets/top-languages.svg."""
import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Alantaaa"
PAT = os.environ.get("GH_PAT", "").strip()
TOKEN = PAT or os.environ.get("GITHUB_TOKEN", "")
# owner = repo milikmu | collaborator = repo orang lain tempat kamu kolaborator | organization_member = repo organisasi
AFFILIATION = os.environ.get("AFFILIATION", "owner,collaborator,organization_member")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "top-languages.svg")

BLUE = "#0072FF"
BG = "#0A0F1E"
MUTED = "#9FB3C8"
SANS = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
EXCLUDE = {"Dockerfile", "Makefile", "Shell"}
CODE_PATH = "M15.22 4.97a.75.75 0 0 1 1.06 0l6.5 6.5a.75.75 0 0 1 0 1.06l-6.5 6.5a.749.749 0 0 1-1.275-.326.75.75 0 0 1 .215-.734L21.19 12l-5.97-5.97a.75.75 0 0 1 0-1.06m-6.44 0a.75.75 0 0 1 0 1.06L2.81 12l5.97 5.97a.749.749 0 0 1-.326 1.275.75.75 0 0 1-.734-.215l-6.5-6.5a.75.75 0 0 1 0-1.06l6.5-6.5a.75.75 0 0 1 1.06 0"
W = 820


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def list_repos():
    if PAT:
        base = f"https://api.github.com/user/repos?per_page=100&visibility=all&affiliation={AFFILIATION}"
    else:
        print("ERROR: secret GH_PAT belum diatur. Tanpa token pribadi, repo private tidak bisa dibaca.", file=sys.stderr)
        print("Buat token (classic, scope: repo) lalu simpan sebagai secret bernama GH_PAT.", file=sys.stderr)
        sys.exit(1)
    page, repos = 1, []
    while True:
        chunk = api(f"{base}&page={page}")
        repos += chunk
        if len(chunk) < 100:
            return repos
        page += 1


def collect():
    totals, used = {}, 0
    for repo in list_repos():
        if repo.get("fork"):
            continue
        if repo["owner"]["login"].lower() == USER.lower() and repo["name"].lower() == USER.lower():
            continue
        try:
            langs = api(repo["languages_url"])
        except Exception as e:  # mis. repo organisasi yang belum di-authorize SSO
            print(f"- {repo['full_name']}: dilewati ({e})")
            continue
        langs = {k: v for k, v in langs.items() if k not in EXCLUDE}
        print(f"- {repo['full_name']} ({'private' if repo.get('private') else 'public'}): {sorted(langs, key=langs.get, reverse=True)[:3]}")
        if langs:
            used += 1
        for lang, size in langs.items():
            totals[lang] = totals.get(lang, 0) + size
    print(f"Repo yang dihitung: {used}")
    return totals


def render(totals):
    total = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:3]
    TRACK_X, TRACK_W, card_y, row_h = 190, 500, 0, 52
    card_h = 52 + row_h * max(len(top), 1) - 8
    H = card_y + card_h
    rows, opac = [], [1.0, 0.8, 0.6]
    for i, (lang, size) in enumerate(top):
        pct = size / total * 100
        y = card_y + 26 + i * row_h
        fw = max(TRACK_W * pct / 100, 8)
        rows.append(f'''
  <text x="28" y="{y + 20}" font-family="{SANS}" font-size="16" font-weight="600" fill="#FFFFFF">{escape(lang)}</text>
  <rect x="{TRACK_X}" y="{y + 6}" width="{TRACK_W}" height="18" rx="9" fill="#111B36" stroke="{BLUE}" stroke-opacity="0.3"/>
  <rect x="{TRACK_X}" y="{y + 6}" width="{fw:.1f}" height="18" rx="9" fill="{BLUE}" opacity="{opac[i]}" filter="url(#glow)"/>
  <text x="{W - 28}" y="{y + 20}" text-anchor="end" font-family="{MONO}" font-size="16" font-weight="700" fill="#FFFFFF">{pct:.1f}%</text>''')
    if not rows:
        rows.append(f'<text x="{W/2}" y="{card_y + card_h/2 + 5}" text-anchor="middle" font-family="{SANS}" font-size="15" fill="{MUTED}">Belum ada data bahasa dari repository.</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Top languages">
  <defs>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b1"/><feGaussianBlur in="SourceGraphic" stdDeviation="1.6" result="b2"/><feMerge><feMergeNode in="b1"/><feMergeNode in="b1"/><feMergeNode in="b2"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="glowIcon" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur in="SourceAlpha" stdDeviation="3" result="b"/><feFlood flood-color="{BLUE}" flood-opacity="0.9"/><feComposite in2="b" operator="in" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="glowText" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur in="SourceAlpha" stdDeviation="3" result="b"/><feFlood flood-color="{BLUE}" flood-opacity="0.95"/><feComposite in2="b" operator="in" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="glowSoft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4"/></filter>
  </defs>
  <rect x="0.5" y="{card_y + .5}" width="{W-1}" height="{card_h - 1}" rx="14" fill="{BG}" stroke="{BLUE}" stroke-opacity="0.45"/>{"".join(rows)}
</svg>
'''


def main():
    try:
        totals = collect()
    except Exception as e:  # jangan timpa file lama jika API gagal
        print("Gagal mengambil data:", e, file=sys.stderr)
        sys.exit(1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(totals))
    print("Top languages:", sorted(totals.items(), key=lambda kv: -kv[1])[:3])


if __name__ == "__main__":
    main()
