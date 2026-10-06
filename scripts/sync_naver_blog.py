#!/usr/bin/env python3
import html, re, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

BLOG_ID="duswl6880"
RSS=f"https://rss.blog.naver.com/{BLOG_ID}.xml"
START="<!-- LATEST_BLOG_POSTS_START -->"
END="<!-- LATEST_BLOG_POSTS_END -->"

req=urllib.request.Request(RSS,headers={"User-Agent":"Mozilla/5.0 (compatible; EllyPilatesBlogSync/1.0)"})
with urllib.request.urlopen(req,timeout=30) as r:
    root=ET.fromstring(r.read())

items=root.findall("./channel/item")[:6]
if len(items)<6:
    raise RuntimeError(f"Expected 6 RSS items, got {len(items)}")

cards=[]
for item in items:
    title=(item.findtext("title") or "").strip()
    link=(item.findtext("link") or "").strip()
    pub=(item.findtext("pubDate") or "").strip()
    desc=(item.findtext("description") or "").strip()
    clean=re.sub(r"<[^>]+>"," ",html.unescape(desc))
    clean=re.sub(r"\s+"," ",clean).strip()
    if len(clean)>110: clean=clean[:107].rstrip()+"…"
    date=pub[:16] if pub else ""
    cards.append(f'''        <article class="blog-latest-card">
          <a href="{html.escape(link,quote=True)}" target="_blank" rel="noopener noreferrer">
            <div class="blog-latest-meta"><span>NAVER BLOG</span><time>{html.escape(date)}</time></div>
            <h3 class="blog-latest-title">{html.escape(title)}</h3>
            <p class="blog-latest-summary">{html.escape(clean)}</p>
            <span class="blog-latest-go">READ MORE ↗</span>
          </a>
        </article>''')

path=Path("blog.html")
text=path.read_text(encoding="utf-8")
replacement=START+"\n"+"\n".join(cards)+"\n        "+END
pattern=re.escape(START)+r".*?"+re.escape(END)
new,n=re.subn(pattern,replacement,text,flags=re.S)
if n!=1: raise RuntimeError("Latest blog markers not found exactly once")
path.write_text(new,encoding="utf-8")
