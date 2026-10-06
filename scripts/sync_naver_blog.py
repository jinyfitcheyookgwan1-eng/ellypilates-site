#!/usr/bin/env python3
import html, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
from email.utils import parsedate_to_datetime

BLOG_ID="duswl6880"
RSS=f"https://rss.blog.naver.com/{BLOG_ID}.xml"
START="<!-- LATEST_BLOG_POSTS_START -->"
END="<!-- LATEST_BLOG_POSTS_END -->"
IMG_DIR=Path("assets/blog")
IMG_DIR.mkdir(parents=True,exist_ok=True)

def fetch(url, referer=None):
    headers={"User-Agent":"Mozilla/5.0 (compatible; EllyPilatesBlogSync/1.0)"}
    if referer: headers["Referer"]=referer
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read(), r.headers.get("Content-Type","")

data,_=fetch(RSS)
root=ET.fromstring(data)
items=root.findall("./channel/item")[:6]
if len(items)<6:
    raise RuntimeError(f"Expected 6 RSS items, got {len(items)}")

cards=[]
keep=set()
for idx,item in enumerate(items,1):
    title=(item.findtext("title") or "").strip()
    link=(item.findtext("link") or "").strip()
    pub=(item.findtext("pubDate") or "").strip()
    desc=(item.findtext("description") or "").strip()
    raw=html.unescape(desc)
    m=re.search(r'<img[^>]+(?:src|data-lazy-src)=["\\\']([^"\\\']+)["\\\']',raw,re.I)
    local_img=""
    if m:
        remote=m.group(1).replace("&amp;","&")
        try:
            blob,ctype=fetch(remote,link or f"https://blog.naver.com/{BLOG_ID}")
            ext=".jpg"
            if "png" in ctype.lower(): ext=".png"
            elif "webp" in ctype.lower(): ext=".webp"
            elif "gif" in ctype.lower(): ext=".gif"
            post_id=re.search(r"/(\\d{8,})(?:\\?|$)",link)
            stem=post_id.group(1) if post_id else f"post-{idx}"
            filename=stem+ext
            (IMG_DIR/filename).write_bytes(blob)
            keep.add(filename)
            local_img=f"assets/blog/{filename}"
        except Exception as e:
            print(f"Thumbnail download failed for {link}: {e}")
    clean=re.sub(r"<[^>]+>"," ",raw)
    clean=re.sub(r"\\s+"," ",clean).strip()
    if len(clean)>110: clean=clean[:107].rstrip()+"…"
    try:
        date=parsedate_to_datetime(pub).strftime("%Y.%m.%d") if pub else ""
    except Exception:
        date=pub[:16] if pub else ""
    thumb=(f'<div class="blog-latest-thumb"><img src="{html.escape(local_img,quote=True)}" alt="{html.escape(title,quote=True)}" loading="lazy" width="800" height="600"></div>' if local_img else "")
    cards.append(f'''        <article class="blog-latest-card">
          <a href="{html.escape(link,quote=True)}" target="_blank" rel="noopener noreferrer">
            {thumb}
            <div class="blog-latest-meta"><span>NAVER BLOG</span><time datetime="{date.replace(".","-")}">{html.escape(date)}</time></div>
            <h3 class="blog-latest-title">{html.escape(title)}</h3>
            <p class="blog-latest-summary">{html.escape(clean)}</p>
            <span class="blog-latest-go">READ MORE ↗</span>
          </a>
        </article>''')

for old in IMG_DIR.iterdir():
    if old.is_file() and old.name not in keep:
        old.unlink()

path=Path("blog.html")
page=path.read_text(encoding="utf-8")
replacement=START+"\n"+"\n".join(cards)+"\n        "+END
pattern=re.escape(START)+r".*?"+re.escape(END)
new,n=re.subn(pattern,replacement,page,flags=re.S)
if n!=1: raise RuntimeError("Latest blog markers not found exactly once")
path.write_text(new,encoding="utf-8")
