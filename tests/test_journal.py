import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

SPEC = importlib.util.spec_from_file_location("journal", Path(__file__).resolve().parents[1] / "scripts" / "build_journal_pages.py")
journal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(journal)

def rss(posts):
    items = []
    for post_id, body in posts:
        items.append(f"<item><title>Test {post_id}</title><link>https://blog.naver.com/duswl6880/{post_id}</link><pubDate>Thu, 08 Oct 2026 12:00:00 +0900</pubDate><description>{body}</description></item>")
    return ("<rss><channel>" + "".join(items) + "</channel></rss>").encode()

class Response:
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.data

class JournalTests(unittest.TestCase):
    def test_archive_persists_and_short_post_remains_external(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "blog.html").write_text('<div><!-- LATEST_BLOG_POSTS_START --><a href="https://blog.naver.com/duswl6880/224416349707" target="_blank" rel="noopener noreferrer">Test</a><!-- LATEST_BLOG_POSTS_END --></div>\n    </section>', encoding="utf-8")
            (root / "sitemap.xml").write_text('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>', encoding="utf-8")
            with patch.object(journal, "ROOT", root), patch.object(journal, "OUT", root / "blog"):
                with patch.object(journal.urllib.request, "urlopen", return_value=Response(rss([("224416349707", "Long text. " * 100), ("224415177780", "Short excerpt")]))):
                    journal.main()
                self.assertTrue((root / "blog" / "224416349707.html").exists())
                self.assertIn('href="blog/224416349707.html"', (root / "blog.html").read_text())
                self.assertIn('224415177780', (root / "blog" / "archive.html").read_text())
                self.assertIn('224416349707.html', (root / "sitemap.xml").read_text())
                ET.parse(root / "sitemap.xml")
                with patch.object(journal.urllib.request, "urlopen", return_value=Response(rss([("224422222222", "New post. " * 100)]))):
                    journal.main()
                self.assertTrue((root / "blog" / "224416349707.html").exists())
                self.assertIn('224416349707.html', (root / "sitemap.xml").read_text())
                self.assertIn('224415177780', (root / "blog" / "archive.html").read_text())
                self.assertIn('224422222222', (root / "blog" / "archive.html").read_text())

if __name__ == "__main__":
    unittest.main()
