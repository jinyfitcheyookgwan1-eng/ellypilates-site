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
MIN_LENGTH = 80

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
    }, ensure_ascii=False).replace("<", "\\u003c")
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
<style>body{{margin:0;background:#faf9f7;color:#302c29;font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}.journal-wrap{{max-width:860px;margin:auto;padding:34px 24px 100px}}.journal-nav{{display:flex;justify-content:space-between;gap:16px;padding-bottom:24px;border-bottom:1px solid #e5dfd8}}.journal-nav a{{color:inherit;text-decoration:none;font-size:13px;letter-spacing:.09em}}.journal-kicker{{font-size:11px;letter-spacing:.25em;color:#8c827a;margin:68px 0 18px}}.journal-content{{max-width:700px;margin:auto}}h1{{font-family:Georgia,"Noto Serif KR",serif;font-size:clamp(29px,4.5vw,44px);line-height:1.5;letter-spacing:-.035em;overflow-wrap:anywhere;margin:20px 0 38px}}article p{{font-size:16px;line-height:2.05;overflow-wrap:anywhere;margin:1.6em 0;color:#4e4843}}.journal-date{{font-size:12px;letter-spacing:.1em;color:#8c827a}}.journal-source{{display:inline-block;margin-top:36px;padding:13px 20px;border:1px solid #b9afa5;text-decoration:none;color:inherit;font-size:13px}}.journal-bottom{{border-top:1px solid #e5dfd8;margin-top:70px;padding-top:24px;font-size:13px}}.journal-bottom a{{color:inherit}}@media(max-width:600px){{.journal-wrap{{padding:24px 20px 70px}}.journal-kicker{{margin-top:48px}}article p{{font-size:15px;line-height:1.95}}}}</style>
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
    OUT.mkdir(exist_ok=True)
    archive_path = OUT / "feed-index.json"
    try:
        archive = json.loads(archive_path.read_text(encoding="utf-8")) if archive_path.exists() else {}
        if not isinstance(archive, dict):
            archive = {}
    except (ValueError, OSError):
        archive = {}
    for item in items:
        title = (item.findtext("title") or "").strip()
        source = (item.findtext("link") or "").strip()
        match = re.search(r"/(\d{8,})(?:\?|$)", source)
        if not match or not source.startswith("https://blog.naver.com/duswl6880/"):
            continue
        body = clean_text(item.findtext("description") or "")
        post_id = match.group(1)
        archive[post_id] = {"title": title, "source": source, "summary": body[:200]}
        if len(body) < MIN_LENGTH:
            continue
        try:
            date = parsedate_to_datetime(item.findtext("pubDate")).date().isoformat()
        except (TypeError, ValueError):
            continue
        eligible[post_id] = (title, body, date, source)
    archive_path.write_text(json.dumps(archive, ensure_ascii=False, indent=2), encoding="utf-8")
    for post_id, (title, body, date, source) in eligible.items():
        (OUT / f"{post_id}.html").write_text(render(title,body,post_id,date,source),encoding="utf-8")
    # Every observed post remains discoverable in the permanent archive,
    # including RSS excerpts too short for an independent SEO article.
    archive_rows = []
    for post_id, info in reversed(list(archive.items())):
        local = OUT / f"{post_id}.html"
        link = f"{post_id}.html" if local.exists() else info["source"]
        title_safe = html.escape(info["title"])
        summary_safe = html.escape(info.get("summary", "")[:115])
        archive_rows.append(
            f'<a class="entry" href="{html.escape(link, quote=True)}">'
            f'<span class="entry-tag">ELLY JOURNAL</span><h2>{title_safe}</h2>'
            f'<p>{summary_safe}</p><span class="entry-more">READ JOURNAL →</span></a>'
        )
    archive_html = ("""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>엘리필라테스 전체 블로그 글 | ELLY JOURNAL</title>
<meta name="description" content="엘리필라테스 삼송역점의 필라테스, 산전·산후 운동, 웰니스와 스튜디오 소식을 만나보세요.">
<link rel="canonical" href="https://ellypilates.co.kr/blog/archive.html">
<style>
*{box-sizing:border-box}body{margin:0;background:#faf9f7;color:#302c29;font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif}
.wrap{max-width:1180px;margin:auto;padding:30px 26px 100px}
nav{display:flex;justify-content:space-between;border-bottom:1px solid #e5dfd8;padding-bottom:25px}
nav a{font-size:13px;letter-spacing:.09em;color:inherit;text-decoration:none}
.eyebrow{font-size:11px;letter-spacing:.25em;color:#93877d;margin-top:90px}
h1{font-family:Georgia,"Noto Serif KR",serif;font-size:clamp(34px,5vw,55px);font-weight:500;margin:16px 0 15px}
.intro{color:#756e68;font-size:15px;line-height:1.9;margin-bottom:65px}
.entries{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}
.entry{display:flex;flex-direction:column;min-height:265px;border:1px solid #e7e1da;background:#fff;padding:29px 26px;color:inherit;text-decoration:none;transition:border-color .2s,transform .2s}
.entry:hover{border-color:#b6a99c;transform:translateY(-3px)}
.entry-tag{font-size:10px;letter-spacing:.18em;color:#9a8c7e}
.entry h2{font-size:19px;font-weight:500;line-height:1.55;letter-spacing:-.035em;margin:20px 0 12px;overflow-wrap:anywhere}
.entry p{font-size:13px;line-height:1.75;color:#82786f;margin:0 0 22px;overflow-wrap:anywhere;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.entry-more{margin-top:auto;font-size:10px;letter-spacing:.13em}
.pager{display:flex;justify-content:center;gap:8px;margin:48px 0 0;flex-wrap:wrap}
.pager button{border:1px solid #ded6cd;background:transparent;padding:10px 14px;cursor:pointer;color:inherit}
.pager button[aria-current="page"]{background:#302c29;color:white}
@media(max-width:900px){.entries{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.wrap{padding:24px 20px 70px}.eyebrow{margin-top:55px}.entries{grid-template-columns:1fr;gap:14px}.entry{min-height:220px}.intro{margin-bottom:35px}}
</style></head><body><main class="wrap"><nav><a href="../index.html">ELLY PILATES</a><a href="../blog.html">← ELLY JOURNAL</a></nav>
<p class="eyebrow">MOVEMENT · WELLNESS · ELLY LIFE</p><h1>ELLY JOURNAL</h1>
<p class="intro">엘리필라테스의 모든 이야기.<br>움직임을 이해하고, 건강한 일상을 만들어가는 기록.</p>
<section class="entries" id="entries" aria-label="전체 블로그 글">""" + "".join(archive_rows) + """</section>
<nav class="pager" id="pager" aria-label="페이지 선택"></nav></main>
<script>
(function(){
const items=[...document.querySelectorAll(".entry")], pager=document.getElementById("pager"), perPage=9;
const count=Math.ceil(items.length/perPage);
function show(page){items.forEach((item,i)=>item.hidden=!(i>=(page-1)*perPage&&i<page*perPage));
pager.replaceChildren();
for(let i=1;i<=count;i++){const b=document.createElement("button");b.textContent=i;b.type="button";
if(i===page)b.setAttribute("aria-current","page");
b.addEventListener("click",()=>{show(i);document.querySelector(".eyebrow").scrollIntoView({behavior:"smooth"})});pager.appendChild(b)}}
show(1);
})();
</script><style>.entry[hidden]{display:none}</style></body></html>""")
    (OUT / "archive.html").write_text(archive_html, encoding="utf-8")
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
    if 'href="blog/archive.html"' not in tail:
        tail = tail.replace('</div>\n    </section>', '</div>\n      <p style="text-align:center;margin:28px 0"><a href="blog/archive.html">전체 블로그 글 보기 →</a></p>\n    </section>', 1)
    index.write_text(before+START+cards+END+tail,encoding="utf-8")
    sitemap = ROOT / "sitemap.xml"
    xml = sitemap.read_text(encoding="utf-8")
    xml = re.sub(r'\s*<!-- ELLY_JOURNAL_START -->.*?<!-- ELLY_JOURNAL_END -->', "", xml, flags=re.S)
    # Retain every previously published article URL, not only the current RSS window.
    published = sorted(p.stem for p in OUT.glob("*.html") if re.fullmatch(r"\d{8,}", p.stem))
    entries = "\n".join([f"  <url><loc>{DOMAIN}/blog/archive.html</loc></url>"] + [f"  <url><loc>{DOMAIN}/blog/{post_id}.html</loc></url>" for post_id in published])
    marker = f"  <!-- ELLY_JOURNAL_START -->\n{entries}\n  <!-- ELLY_JOURNAL_END -->\n"
    xml = xml.replace("</urlset>", marker+"</urlset>")
    ET.fromstring(xml)
    sitemap.write_text(xml,encoding="utf-8")
    print(f"Updated {len(eligible)} substantial articles; {len(published)} total archived article URLs. Short excerpts link to Naver.")

if __name__ == "__main__":
    main()
