"""
K2 — Keşif (Discovery)
Google Programmable Search JSON API (site-kısıtlı whitelist) ile sorguya uygun
ürün URL'lerini bulur. API anahtarları .env'den okunur.

Kullanım:
    python backend/search.py "erkek beyaz spor ayakkabı"
    python backend/search.py "erkek beyaz spor ayakkabı" 10   # istenen sonuç sayısı
"""
from __future__ import annotations

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY", "")
CSE_ID = os.getenv("GOOGLE_CSE_ID", "")
ENDPOINT = "https://www.googleapis.com/customsearch/v1"

# Whitelist, arama motorunun (CSE) kendi ayarında da tanımlı olmalı; burada
# ekstra güvenlik için site filtresi de uygulanabilir.
WHITELIST = ["trendyol.com", "hepsiburada.com", "n11.com"]


def search(query: str, want: int = 10) -> list[dict]:
    """Sorgu için ürün linklerini döner: [{title, link, snippet, site}]."""
    if not API_KEY or not CSE_ID:
        raise RuntimeError(
            "GOOGLE_API_KEY / GOOGLE_CSE_ID eksik. .env dosyasını doldurun "
            "(.env.example'a bakın)."
        )
    results: list[dict] = []
    start = 1
    with httpx.Client(timeout=20.0) as client:
        while len(results) < want and start <= 91:  # API en fazla 100 sonuç
            params = {
                "key": API_KEY,
                "cx": CSE_ID,
                "q": query,
                "num": min(10, want - len(results)),
                "start": start,
                "hl": "tr",
                "gl": "tr",
            }
            r = client.get(ENDPOINT, params=params)
            r.raise_for_status()
            items = r.json().get("items", [])
            if not items:
                break
            for it in items:
                link = it.get("link", "")
                site = next((w for w in WHITELIST if w in link), None)
                if site:  # sadece whitelist
                    results.append(
                        {
                            "title": it.get("title"),
                            "link": link,
                            "snippet": it.get("snippet"),
                            "site": site,
                        }
                    )
            start += 10
    return results[:want]


def main() -> int:
    if len(sys.argv) < 2:
        print('Kullanım: python backend/search.py "sorgu" [adet]', file=sys.stderr)
        return 2
    query = sys.argv[1]
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    for i, hit in enumerate(search(query, want), 1):
        print(f"{i:2}. [{hit['site']}] {hit['title']}\n    {hit['link']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
