#!/usr/bin/env python3
"""Build indexable journal articles only when the RSS contains substantial text.

Short RSS excerpts keep linking to the original Naver post. This script runs
after the existing RSS card synchronizer; it never scrapes protected Naver pages.
"""
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://ellypilates.co.kr"
RSS = "https://rss.blog.naver.com/duswl6880.xml"
OUT = ROOT / "blog"
START = "<!-- LATEST_BLOG_POSTS_START -->"
END = "<!-- LATEST_BLOG_POSTS_END -->"
MIN_LENGTH = 450

def clean_text(value):
    value = re.sub(r"(?i)<(script|style)[^>]*>.*?</\1>", " ", value, flags=re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def render(title, body, post_id, date, source):
    url = f"{DOMAIN}/blog/{post_id}.html"
    description = body[:150]
    safe = lambda s: html.escape(s, quote=True)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if len(paragraphs) == 1:
        paragraphs = [body[i:i+350] for i in range(0, len(body), 350)]
    article = "\n".join(f"<p>{safe(p)}</p>" for p in paragraphs)
    structured = json.dumps({
        "@context":"https://schema.org","@type":"BlogPosting",
        "headline":title,"description":description,"datePublished":date,
        "mainEntityOfPage":url,"url":url,
        "publisher":{"@type":"Organization","name":"엘리필라테스 삼송역점","url":DOMAIN},
        "isBasedOn":source
    }, ensure_ascii=False).replace("<", "\u003c")
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe(title)} | 엘리필라테스</title>
<meta name="description" content="{safe(description)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:title" content="{safe(title)}">
<meta property="og:description" content="{safe(description)}"><meta property="og:url" content="{url}">
<link rel="stylesheet" href="../styles.css">
<script type="application/ld+json">{structured}</script>
<style>body{{margin:0;background:#fff;color:#252525;font-family:system-ui,sans-serif}}.journal-wrap{{max-width:800px;margin:auto;padding:30px 22px 90px}}.journal-nav{{display:flex;justify-content:space-between;gap:16px;margin-bottom:70px}}.journal-nav a{{color:inherit;text-decoration:none}}h1{{font-size:clamp(26px,4vw,40px);line-height:1.45}}article p{{line-height:2;overflow-wrap:anywhere;margin:1.4em 0}}.journal-date{{color:#666}}.journal-source{{display:inline-block;margin-top:32px;text-decoration:underline;color:inherit}}</style>
</head><body><main class="journal-wrap"><nav class="journal-nav"><a href="../index.html">ELLY PILATES</a><a href="../blog.html">← ELLY JOURNAL</a></nav>
<article><p class="journal-date">{safe(date)}</p><h1>{safe(title)}</h1>{article}
<a class="journal-source" href="{safe(source)}" rel="noopener noreferrer" target="_blank">네이버 블로그 원문 보기 ↗</a></article></main></body></html>
"""

def main():
    request = urllib.request.Request(RSS, headers={"User-Agent":"Mozilla/5.0 (compatible; EllyJournal/1.0)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())
    items = root.findall("./channel/item")
    if not items:
        raise RuntimeError("RSS returned no posts; leaving files unchanged")
    eligible = {}
    for item in items:
        title = (item.findtext("title") or "").strip()
        source = (item.findtext("link") or "").strip()
        match = re.search(r"/(\d{8,})(?:\?|$)", source)
        if not match or not source.startswith("https://blog.naver.com/duswl6880/"):
            continue
        body = clean_text(item.findtext("description") or "")
        if len(body) < MIN_LENGTH:
            continue
        try:
            date = parsedate_to_datetime(item.findtext("pubDate")).date().isoformat()
        except (TypeError, ValueError):
            continue
        eligible[match.group(1)] = (title, body, date, source)
    OUT.mkdir(exist_ok=True)
    for post_id, (title, body, date, source) in eligible.items():
        (OUT / f"{post_id}.html").write_text(render(title,body,post_id,date,source),encoding="utf-8")
    index = ROOT / "blog.html"
    page = index.read_text(encoding="utf-8")
    before, separator, rest = page.partition(START)
    if not separator or END not in rest:
        raise RuntimeError("Cannot locate blog card markers")
    cards, tail = rest.split(END, 1)
    for post_id in eligible:
        cards = re.sub(
            r'href="https://blog\.naver\.com/duswl6880/' + post_id + r'[^"]*" target="_blank" rel="noopener noreferrer"',
            f'href="blog/{post_id}.html"', cards)
    index.write_text(before+START+cards+END+tail,encoding="utf-8")
    sitemap = ROOT / "sitemap.xml"
    xml = sitemap.read_text(encoding="utf-8")
    xml = re.sub(r'\s*<!-- ELLY_JOURNAL_START -->.*?<!-- ELLY_JOURNAL_END -->', "", xml, flags=re.S)
    # Retain every previously published article URL, not only the current RSS window.
    published = sorted(p.stem for p in OUT.glob("*.html") if re.fullmatch(r"\d{8,}", p.stem))
    entries = "\n".join(f"  <url><loc>{DOMAIN}/blog/{post_id}.html</loc></url>" for post_id in published)
    marker = f"  <!-- ELLY_JOURNAL_START -->\n{entries}\n  <!-- ELLY_JOURNAL_END -->\n"
    xml = xml.replace("</urlset>", marker+"</urlset>")
    ET.fromstring(xml)
    sitemap.write_text(xml,encoding="utf-8")
    print(f"Updated {len(eligible)} substantial articles; {len(published)} total archived article URLs. Short excerpts link to Naver.")

if __name__ == "__main__":
    main()
