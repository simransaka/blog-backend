from src.tools.fetch_page import fetch_page


def test_fetch_page():
    url = "https://example.com"

    text = fetch_page(url)

    assert isinstance(text, str)
    assert len(text) > 0

    print(text)