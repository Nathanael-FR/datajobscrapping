import httpx
from selectolax.parser import HTMLParser
import re


def scrape_prog_lang() -> list[str]:
    """Scrape programming languages from Wikipedia"""

    url = "https://fr.wikipedia.org/wiki/Liste_de_langages_de_programmation"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
    }

    resp = httpx.get(url, headers=headers)
    resp.raise_for_status()

    html = HTMLParser(resp.text)

    pattern = re.compile(r"\(.*?\)")

    # Retrieve all li elements with no class that contain an anchor tag with an href attribute starting with /wiki/
    langs = [
        lang.text(deep=True).strip()
        for lang in html.css("li:not([class]) a[href^='/wiki/']")
    ]

    # Remove text between parentheses and parentheses:
    langs = [pattern.sub("", lang) for lang in langs if lang not in ["M", "D"]]

    # Troncate the list whenever an empty string is found
    langs = langs[:langs.index("")]

    return langs


if __name__ == "__main__":
    langs = scrape_prog_lang()
    print(langs)
