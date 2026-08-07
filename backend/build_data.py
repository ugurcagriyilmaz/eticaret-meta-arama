"""
build_data.py — Boru hattı (pipeline) orkestrasyonu
understand (K1) -> search (K2) -> extract (K3) -> match (K4) -> data/data.json (K5 için)

Kullanım:
    python backend/build_data.py "beyaz erkek spor ayakkabı beden 42"
    python backend/build_data.py "..." --limit 8

Cache: data/cache/<hash>.json (aynı URL tekrar çekilmez). robots.txt'ye saygı
gösterilir; hız düşük tutulur.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.robotparser as robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from understand import understand
from match import match, slug_ok
import extract as extract_mod

try:
    from search import search
except Exception:  # noqa: BLE001 - playwright yoksa arama atlansın, boru hattı çökmesin
    search = None  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = DATA / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

DELAY_SN = 2.0  # nazik hız
_robots_cache: dict[str, robotparser.RobotFileParser] = {}


def _robots_lines(base: str) -> list[str] | None:
    """robots.txt'yi curl_cffi ile çeker (bu siteler urllib'e 403 verir; o yüzden
    stdlib robotparser.read() kullanılamaz — 403'te 'hepsini yasakla'ya düşer)."""
    try:
        from curl_cffi import requests as cffi

        r = cffi.get(base + "/robots.txt", impersonate="chrome", timeout=15)
        if r.status_code == 200 and r.text:
            return r.text.splitlines()
    except Exception:  # noqa: BLE001
        pass
    return None


def robots_ok(url: str) -> bool:
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    rp = _robots_cache.get(base)
    if rp is None:
        lines = _robots_lines(base)
        if lines is None:
            rp = None  # okunamadıysa engelleme (demo, düşük hız + cache)
        else:
            rp = robotparser.RobotFileParser()
            rp.parse(lines)
        _robots_cache[base] = rp  # type: ignore
    if rp is None:
        return True
    return rp.can_fetch(extract_mod.HEADERS["User-Agent"], url)


def cached_extract(url: str) -> dict:
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    cf = CACHE / f"{key}.json"
    if cf.exists():
        return json.loads(cf.read_text(encoding="utf-8"))
    data = extract_mod.extract(url)
    cf.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def _balanced(hits: list[dict], limit: int) -> list[str]:
    """Sitelere göre round-robin seçim — tek site tüm limiti doldurmasın
    (meta-arama = her siteden temsil)."""
    from collections import defaultdict, deque

    bysite: dict[str, deque] = defaultdict(deque)
    for h in hits:
        bysite[h["site"]].append(h["link"])
    out: list[str] = []
    while len(out) < limit and any(bysite.values()):
        for site in list(bysite):
            if bysite[site]:
                out.append(bysite[site].popleft())
                if len(out) >= limit:
                    break
    return out


def _search_terms(query: str, attrs: dict) -> str:
    """Site aramaları anahtar-kelime tabanlı: ham cümle ('...beden 42') yerine
    attribute'lardan temiz sorgu kur ('beyaz erkek spor ayakkabı') → alaka artar."""
    terms = [attrs.get("renk"), attrs.get("cinsiyet"), attrs.get("kategori"), attrs.get("model")]
    clean = " ".join(t for t in terms if t)
    return clean or query


def build(query: str, limit: int = 8, delay: float = DELAY_SN) -> dict:
    attrs = understand(query)
    urls: list[str] = []
    if search is not None:
        try:
            # geniş aday havuzu çek; kategoriye göre ön-ele; site-dengeli seç
            hits = search(_search_terms(query, attrs), want=limit * 4)
            urls = _balanced(
                [h for h in hits if slug_ok(h["link"], attrs)], limit
            )
        except Exception as e:  # noqa: BLE001
            print(f"[uyarı] arama atlandı: {e}")
    products = []
    for url in urls:
        if not robots_ok(url):
            print(f"[robots] atlandı: {url}")
            continue
        try:
            products.append(cached_extract(url))
        except Exception as e:  # noqa: BLE001
            print(f"[extract hata] {url}: {e}")
        time.sleep(delay)

    ranked = match(products, attrs)
    # sunum için sadeleştirilmiş kayıtlar (K5 index.html bunu okur)
    items = [
        {
            "ad": p.get("ad"),
            "fiyat": p.get("fiyat"),
            "para_birimi": p.get("para_birimi") or "TRY",
            "site": urlparse(p.get("url", "")).netloc.replace("www.", ""),
            "link": p.get("url"),
            "gorsel": p.get("gorsel"),
            "skor": p.get("_skor", 0),
        }
        for p in ranked
        if p.get("ad")
    ]
    return {
        "sorgu": query,
        "attributes": attrs,
        "guncelleme": datetime.now(timezone.utc).isoformat(),
        "adet": len(items),
        "urunler": items,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="beyaz erkek spor ayakkabı beden 42")
    ap.add_argument("--limit", type=int, default=8)
    args = ap.parse_args()

    out = build(args.query, args.limit)
    (DATA / "data.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"data/data.json yazıldı — {out['adet']} ürün (sorgu: {out['sorgu']!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
