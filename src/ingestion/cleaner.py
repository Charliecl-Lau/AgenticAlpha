import re
from bs4 import BeautifulSoup
import markdownify


def _process_markdown(md: str) -> str:
    """Collapse excessive blank lines and unescape markdown special chars."""
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    # Unescape markdown special characters that don't need escaping in plain text
    md = md.replace(r"\.", ".").replace(r"\*", "*").replace(r"\[", "[").replace(r"\]", "]")
    return md


def _strip_boilerplate(soup: BeautifulSoup) -> None:
    """Remove nav, footer, header, aside, script, style tags and ad/cookie/banner elements."""
    for tag in soup.find_all(["nav", "footer", "header", "aside", "script", "style"]):
        tag.decompose()
    for sel in [".ad", ".advertisement", "[class*='cookie']", "[class*='banner']"]:
        for el in soup.select(sel):
            el.decompose()


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    _strip_boilerplate(soup)
    md = markdownify.markdownify(str(soup), heading_style="ATX")
    md = _process_markdown(md)
    return md


def extract_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    _strip_boilerplate(soup)
    root = soup.find("article") or soup.find("main") or soup.find("body")
    if root is None:
        return html_to_markdown(html)
    md = markdownify.markdownify(str(root), heading_style="ATX")
    md = _process_markdown(md)
    return md
