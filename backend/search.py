"""
K2 — Keşif (Discovery)  [Headless tarayıcı ile site araması]

TR e-ticaret siteleri (Trendyol/Hepsiburada/n11) SPA + agresif anti-bot:
- Ürün SAYFALARI curl_cffi ile açılıyor (bkz. extract.py) ama ARAMA sayfaları
  düz HTTP'ye 403 veriyor ve sonuçlar JS ile render ediliyor.
- Çözüm: Playwright + gerçek Chromium. Arama sayfasını açar, JS render'ı bekler,
  DOM'daki ürün linklerini toplar. Google API'ye gerek yok.

Lokal toplayıcıda çalışır (ev IP'si). Kullanım:
    python backend/search.py "beyaz erkek spor ayakkabı"
    python backend/search.py "..." 9
"""
from __future__ import annotations

import re
import sys
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Her site: arama URL şablonu + ürün linki DOM seçicisi + doğrulama regex'i.
# Site tasarımı değişirse yalnızca 'selector'/'pattern' güncellenir.
SITES: dict[str, dict[str, str]] = {
    "trendyol.com": {
        "url": "https://www.trendyol.com/sr?q={q}",
        "selector": "a[href*='-p-']",
        "pattern": r"-p-\d+",
    },
    "hepsiburada.com": {
        "url": "https://www.hepsiburada.com/ara/?q={q}",
        "selector": "a[href*='-p-']",
        "pattern": r"-p-[A-Za-z0-9]+",
    },
    "n11.com": {
        "url": "https://www.n11.com/arama?q={q}",
        "selector": "a[href*='/urun/']",
        "pattern": r"/urun/",
    },
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
NAV_TIMEOUT = 25_000  # ms


def _clean(url: str) -> str:
    return url.split("?")[0].split("#")[0]


def _collect(page, cfg: dict) -> list[str]:
    """Arama sayfasındaki DOM'dan ürün linklerini toplar (JS render sonrası)."""
    try:
        page.wait_for_selector(cfg["selector"], timeout=NAV_TIMEOUT)
    except PWTimeout:
        pass  # yine de o ana kadarki DOM'u tara
    hrefs = page.eval_on_selector_all(
        cfg["selector"], "els => els.map(e => e.href)"
    )
    pat = re.compile(cfg["pattern"])
    out: list[str] = []
    for h in hrefs:
        if h and pat.search(h):
            out.append(_clean(h))
    return out


def search(query: str, want: int = 9) -> list[dict]:
    """Sorgu için whitelist sitelerinden ürün linkleri: [{link, site}] (dedup)."""
    results: list[dict] = []
    seen: set[str] = set()
    per_site = max(2, want // len(SITES) + 1)
    q = quote_plus(query)

    with sync_playwright() as p:
        # NOT: headless=False zorunlu. Hepsiburada (Akamai tarzı güvenlik duvarı)
        # gerçek/görünür tarayıcı ister; headless'te "Güvenlik" sayfasına düşer.
        # Toplayıcı lokalde koştuğu için görünür pencere sorun değil.
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="tr-TR",
            user_agent=UA,
            viewport={"width": 1366, "height": 768},
            extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"},
        )
        # webdriver izini gizle
        context.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        page = context.new_page()

        for site, cfg in SITES.items():
            url = cfg["url"].format(q=q)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
                links = _collect(page, cfg)
            except Exception as e:  # noqa: BLE001 - bir site düşerse diğerine devam
                print(f"[uyarı] {site} arama hatası: {str(e)[:80]}")
                continue
            found = 0
            for link in links:
                if link in seen:
                    continue
                seen.add(link)
                results.append({"link": link, "site": site})
                found += 1
                if found >= per_site:
                    break

        context.close()
        browser.close()
    return results[:want]


def main() -> int:
    if len(sys.argv) < 2:
        print('Kullanım: python backend/search.py "sorgu" [adet]', file=sys.stderr)
        return 2
    query = sys.argv[1]
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    hits = search(query, want)
    for i, h in enumerate(hits, 1):
        print(f"{i:2}. [{h['site']}] {h['link']}")
    if not hits:
        print("Sonuç yok — seçici güncellenmeli ya da site engelledi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
