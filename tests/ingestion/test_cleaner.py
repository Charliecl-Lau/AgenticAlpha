from src.ingestion.cleaner import html_to_markdown, extract_article_text


def test_html_to_markdown_strips_nav_and_footer():
    html = (
        "<html><nav>Site nav</nav>"
        "<article><p>CATL reported strong Q3 margins.</p></article>"
        "<footer>Copyright 2024</footer></html>"
    )
    md = html_to_markdown(html)
    assert "CATL reported strong Q3 margins" in md
    assert "Site nav" not in md
    assert "Copyright" not in md


def test_html_to_markdown_collapses_excess_blank_lines():
    html = "<p>First.</p><br><br><br><br><p>Second.</p>"
    md = html_to_markdown(html)
    assert md.count("\n\n\n") == 0


def test_extract_article_text_prefers_article_tag():
    html = (
        "<html><body>"
        "<div class='ad'>Buy stuff now!</div>"
        "<article><h1>LGES IRA Update</h1><p>LGES secured $1.2B credits.</p></article>"
        "</body></html>"
    )
    text = extract_article_text(html)
    assert "LGES secured $1.2B credits" in text
    assert "Buy stuff now" not in text


def test_extract_article_text_falls_back_to_body():
    html = "<html><body><p>Earnings summary here.</p></body></html>"
    text = extract_article_text(html)
    assert "Earnings summary here" in text


def test_html_to_markdown_strips_header_and_aside():
    html = (
        "<html><header>Site header</header>"
        "<aside>Sidebar</aside>"
        "<article><p>Content here.</p></article></html>"
    )
    md = html_to_markdown(html)
    assert "Content here" in md
    assert "Site header" not in md
    assert "Sidebar" not in md


def test_html_to_markdown_strips_ad_selectors():
    html = (
        "<html><body>"
        "<div class='advertisement'>Ad content</div>"
        "<div class='cookie-notice'>Cookie banner</div>"
        "<div class='banner-top'>Top banner</div>"
        "<p>Real content.</p>"
        "</body></html>"
    )
    md = html_to_markdown(html)
    assert "Real content" in md
    assert "Ad content" not in md
    assert "Cookie banner" not in md
    assert "Top banner" not in md


def test_extract_article_text_falls_back_to_html_to_markdown_on_empty():
    html = "<html></html>"
    text = extract_article_text(html)
    assert isinstance(text, str)
