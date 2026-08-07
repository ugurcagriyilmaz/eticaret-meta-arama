"""
K3 — Çıkarım (Extraction)
Verilen ürün URL'ini çeker, gömülü JSON-LD (schema.org Product/Offer) parse eder,
{ad, fiyat, para_birimi, marka, gorsel, stok, url} döner. JSON-LD yoksa temel CSS fallback dener.

Kullanım:
    python backend/extract.py <url>
"""
from __future__ import annotations

import json
import sys
import time
from typing import Any, Optional

import httpx
import extruct
from bs4 import BeautifulSoup
from w3lib.html import get_base_url

# Gerçek tarayıcıya benzeyen başlıklar (anti-bot toleransı için)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = 20.0


def fetch(url: str) -> tuple[str, str]:
    """Sayfayı indirir; (html, final_url) döner.

    Önce curl_cffi (Chrome TLS/JA3 taklidi) denenir — TR e-ticaret siteleri düz
    HTTP istemcilerini 403 ile engelliyor; tarayıcı parmak-izi bunu aşar.
    curl_cffi yoksa/başarısızsa httpx'e düşer.
    """
    try:
        from curl_cffi import requests as cffi
        from curl_cffi.requests.exceptions import SSLError, ConnectionError as CErr

        last_err: Exception = RuntimeError("fetch")
        for attempt in range(4):
            try:
                r = cffi.get(
                    url,
                    impersonate="chrome",
                    timeout=TIMEOUT,
                    headers={"Accept-Language": HEADERS["Accept-Language"]},
                )
                r.raise_for_status()
                return r.text, str(r.url)
            except (SSLError, CErr) as e:  # GoodbyeDPI kaynakli flaky TLS
                last_err = e
                time.sleep(1.0)
        raise last_err
    except Exception:
        with httpx.Client(
            headers=HEADERS, timeout=TIMEOUT, follow_redirects=True
        ) as client:
            r = client.get(url)
            r.raise_for_status()
            return r.text, str(r.url)


def _first(value: Any) -> Any:
    """schema.org alanları çoğu zaman liste döner; ilk anlamlı elemanı al."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _text(value: Any) -> Optional[str]:
    value = _first(value)
    if value is None:
        return None
    if isinstance(value, dict):
        # {"@value": "..."} veya {"name": "..."} gibi
        return value.get("name") or value.get("@value") or None
    return str(value).strip() or None


def _parse_offer(offer: Any) -> dict[str, Optional[str]]:
    offer = _first(offer) or {}
    if not isinstance(offer, dict):
        return {"fiyat": None, "para_birimi": None, "stok": None}
    fiyat = offer.get("price") or offer.get("lowPrice") or offer.get("highPrice")
    if isinstance(fiyat, dict):
        fiyat = fiyat.get("@value")
    stok = _text(offer.get("availability"))
    if stok:
        stok = stok.rsplit("/", 1)[-1]  # http://schema.org/InStock -> InStock
    return {
        "fiyat": str(fiyat).strip() if fiyat is not None else None,
        "para_birimi": _text(offer.get("priceCurrency")),
        "stok": stok,
    }


def _find_product(data: dict) -> Optional[dict]:
    """extruct çıktısından ilk Product tipli node'u bulur (JSON-LD öncelikli)."""
    def is_product(node: Any) -> bool:
        if not isinstance(node, dict):
            return False
        t = node.get("@type") or node.get("type")
        if isinstance(t, list):
            return any("Product" in str(x) for x in t)
        return "Product" in str(t or "")

    for syntax in ("json-ld", "microdata", "rdfa", "opengraph"):
        for node in data.get(syntax, []):
            # JSON-LD @graph desteği
            graph = node.get("@graph") if isinstance(node, dict) else None
            candidates = graph if isinstance(graph, list) else [node]
            for c in candidates:
                if is_product(c):
                    return c
    return None


def from_structured(html: str, url: str) -> Optional[dict]:
    base_url = get_base_url(html, url)
    data = extruct.extract(
        html, base_url=base_url, syntaxes=["json-ld", "microdata", "rdfa", "opengraph"]
    )
    product = _find_product(data)
    if not product:
        return None
    offer = _parse_offer(product.get("offers"))
    gorsel = product.get("image")
    if isinstance(gorsel, dict):
        gorsel = gorsel.get("url") or gorsel.get("@value")
    return {
        "ad": _text(product.get("name")),
        "fiyat": offer["fiyat"],
        "para_birimi": offer["para_birimi"],
        "marka": _text(product.get("brand")),
        "gorsel": _first(gorsel),
        "stok": offer["stok"],
        "url": url,
        "kaynak": "json-ld/microdata",
    }


def _price_from_embedded(html: str) -> Optional[str]:
    """Bazı siteler (ör. n11) fiyatı JSON-LD'de değil, sayfa içindeki JSON
    state'inde tutar. Yapısal veri + meta + CSS başarısızsa son çare olarak
    gömülü JSON'dan fiyatı çeker. 'displayPriceFloat' = gösterilen/indirimli
    fiyat (kullanıcının ödediği) tercih edilir; yoksa 'priceFloat' (liste)."""
    import re

    for key in ("displayPriceFloat", "priceFloat"):
        m = re.search(rf'"{key}"\s*:\s*([0-9]+(?:\.[0-9]+)?)', html)
        if m:
            return m.group(1)
    # "price":"1.979,64 TL" biçimi → 1979.64
    m = re.search(r'"price"\s*:\s*"([\d.,]+)\s*TL"', html)
    if m:
        return m.group(1).replace(".", "").replace(",", ".")
    return None


def from_css(html: str, url: str) -> dict:
    """JSON-LD yoksa temel CSS/meta fallback (kaba, siteye göre gevşek)."""
    soup = BeautifulSoup(html, "lxml")

    def meta(prop: str) -> Optional[str]:
        el = soup.find("meta", attrs={"property": prop}) or soup.find(
            "meta", attrs={"name": prop}
        )
        return el.get("content").strip() if el and el.get("content") else None

    ad = meta("og:title") or (soup.title.string.strip() if soup.title else None)
    gorsel = meta("og:image")
    # Yaygın fiyat ipuçları
    fiyat = (
        meta("product:price:amount")
        or meta("og:price:amount")
    )
    para = meta("product:price:currency") or meta("og:price:currency")
    if not fiyat:
        el = soup.select_one(
            "[itemprop=price], .price, .prc-dsc, .product-price, [data-price]"
        )
        if el:
            fiyat = (el.get("content") or el.get("data-price") or el.get_text()).strip()
    if not fiyat:
        fiyat = _price_from_embedded(html)  # gömülü JSON (n11 vb.) — son çare
    return {
        "ad": ad,
        "fiyat": fiyat,
        "para_birimi": para or ("TRY" if fiyat else None),
        "marka": meta("og:site_name"),
        "gorsel": gorsel,
        "stok": None,
        "url": url,
        "kaynak": "css-fallback",
    }


def extract(url: str) -> dict:
    """Ana giriş: bir ürün URL'i -> normalize edilmiş ürün sözlüğü."""
    html, final_url = fetch(url)
    result = from_structured(html, final_url)
    if result and result.get("ad") and result.get("fiyat"):
        return result
    # yapısal veri eksikse fallback ile birleştir
    fb = from_css(html, final_url)
    if result:
        for k, v in fb.items():
            if not result.get(k):
                result[k] = v
        result["kaynak"] = "json-ld+fallback"
        return result
    return fb


def main() -> int:
    if len(sys.argv) < 2:
        print("Kullanım: python backend/extract.py <url>", file=sys.stderr)
        return 2
    url = sys.argv[1]
    try:
        data = extract(url)
    except httpx.HTTPError as e:
        print(json.dumps({"hata": f"fetch: {e}", "url": url}, ensure_ascii=False))
        return 1
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
