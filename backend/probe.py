"""
probe.py — Hangi siteler "temiz" parse ediliyor?
Verilen URL listesi için extract.py'yi koşturur, her URL için
kaynak (json-ld/css) + kritik alanların dolu olup olmadığını tablo olarak raporlar.

Kullanım:
    python backend/probe.py                 # gömülü örnek URL listesi
    python backend/probe.py urls.txt        # her satırda bir URL
"""
from __future__ import annotations

import sys
from urllib.parse import urlparse

from extract import extract

# Test için birkaç örnek ürün URL'i (whitelist siteleri).
# NOT: bu URL'ler zamanla ölebilir; probe amacı mekanizmayı doğrulamak.
ORNEK_URLLER = [
    "https://www.trendyol.com/",
    "https://www.hepsiburada.com/",
    "https://www.n11.com/",
]


def load_urls(argv: list[str]) -> list[str]:
    if len(argv) >= 2:
        with open(argv[1], "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    return ORNEK_URLLER


def domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def main() -> int:
    urls = load_urls(sys.argv)
    rows = []
    for url in urls:
        try:
            d = extract(url)
            ok = bool(d.get("ad") and d.get("fiyat"))
            rows.append(
                (domain(url), "OK" if ok else "EKSİK", d.get("kaynak", "-"),
                 (d.get("ad") or "")[:32], d.get("fiyat") or "-", d.get("para_birimi") or "-")
            )
        except Exception as e:  # noqa: BLE001 - rapor amaçlı geniş yakalama
            rows.append((domain(url), "HATA", str(e)[:30], "-", "-", "-"))

    hdr = ("SITE", "DURUM", "KAYNAK", "AD", "FIYAT", "PB")
    widths = [max(len(str(r[i])) for r in ([hdr] + rows)) for i in range(len(hdr))]
    line = lambda r: "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r))
    print(line(hdr))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print(line(r))
    temiz = sum(1 for r in rows if r[1] == "OK")
    print(f"\nTemiz parse: {temiz}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
