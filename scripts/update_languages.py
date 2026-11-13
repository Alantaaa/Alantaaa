#!/usr/bin/env python3
"""Hitung 3 bahasa pemrograman teratas dari repo publik lalu tulis assets/top-languages.svg."""
import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Alantaaa"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "top-languages.svg")

BLUE = "#0072FF"
BG = "#0A0F1E"
TXT = "#E6EDF3"
MUTED = "#9FB3C8"
SANS = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
EXCLUDE = {"Dockerfile", "Makefile", "Shell"}  # bukan "bahasa utama" untuk profil


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    totals = {}
    page = 1
    while True:
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        if not repos:
            break
        for repo in repos:
            if repo.get("fork") or repo["name"].lower() == USER.lower():
                continue
            for lang, size in api(repo["languages_url"]).items():
                if lang in EXCLUDE:
                    continue
                totals[lang] = totals.get(lang, 0) + size
        if len(repos) < 100:
            break
        page += 1
    return totals


def render(totals):
    total = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:3]
    W, TRACK_X, TRACK_W = 820, 190, 500
    row_h, top_pad = 52, 26
    H = top_pad * 2 + row_h * max(len(top), 1) - 8
    rows = []
    opac = [1.0, 0.75, 0.55]
    for i, (lang, size) in enumerate(top):
        pct = size / total * 100
        y = top_pad + i * row_h
        fill_w = max(TRACK_W * pct / 100, 6)
        rows.append(f'''
  <text x="28" y="{y + 20}" font-family="{SANS}" font-size="16" font-weight="600" fill="{TXT}">{escape(lang)}</text>
  <rect x="{TRACK_X}" y="{y + 6}" width="{TRACK_W}" height="18" rx="9" fill="#111B36" stroke="{BLUE}" stroke-opacity="0.25"/>
  <rect x="{TRACK_X}" y="{y + 6}" width="{fill_w:.1f}" height="18" rx="9" fill="{BLUE}" opacity="{opac[i]}"/>
  <text x="{W - 28}" y="{y + 20}" text-anchor="end" font-family="{MONO}" font-size="16" font-weight="600" fill="{TXT}">{pct:.1f}%</text>''')
    if not rows:
        rows.append(f'<text x="{W/2}" y="{H/2 + 5}" text-anchor="middle" font-family="{SANS}" font-size="15" fill="{MUTED}">Belum ada data bahasa dari repository publik.</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Top languages">
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="{BG}" stroke="{BLUE}" stroke-opacity="0.35"/>{"".join(rows)}
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
