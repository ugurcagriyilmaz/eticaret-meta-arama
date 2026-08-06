"""
K4 — Eşleştirme (Matching)  [YER TUTUCU]
Çıkarılan ürünleri, istenen attribute'lara göre filtreler/puanlar.
Şimdilik kural-tabanlı; ileride LLM ile değişecek (imza sabit).

    match(products: list[dict], attrs: dict) -> list[dict]  # skorla sıralı
    slug_ok(url, attrs) -> bool                             # ucuz URL ön-elemesi

Kategori tutarlılığı: "spor ayakkabı" istenince çorap/şapka/sweatshirt gibi
alakasız ürünler elenir (site aramaları bunları da getirebiliyor).
"""
from __future__ import annotations

from understand import fold

# Katlanmış (ASCII) kökler
AYAKKABI = ("ayakkabi", "sneaker", "bot")
# Ayakkabı sorgusunda ürün adında/URL'inde görülürse "bu ayakkabı değil" sayılır
AYAKKABI_DISI = (
    "corap", "socks", "sapka", "bere", "atki", "eldiven", "sweatshirt",
    "tisort", "t-shirt", "forma", "kemer", "canta", "sort", "hoodie",
    "bileklik", "kolye", "mont", "esofman",
)


def _footwear_query(attrs: dict) -> bool:
    kat = fold(str(attrs.get("kategori") or ""))
    return any(f in kat for f in AYAKKABI)


def _coherent(hay: str, attrs: dict) -> bool:
    """Kategori tutarlı mı? (ayakkabı isteniyorsa gerçekten ayakkabı mı)"""
    if not _footwear_query(attrs):
        return True
    if any(n in hay for n in AYAKKABI_DISI):
        return False
    return any(f in hay for f in AYAKKABI)


def slug_ok(url: str, attrs: dict) -> bool:
    """Çıkarımdan ÖNCE ucuz eleme: yalnızca AÇIKÇA alakasız slug'ları at
    (çorap/şapka vb.). Pozitif kök ZORUNLU değil — 'nike-air-max-90' gibi
    marka-adı slug'lı gerçek ayakkabılar elenmesin; pozitif kontrol adımı
    ürün ADI üzerinden _score'da yapılır."""
    if not _footwear_query(attrs):
        return True
    return not any(n in fold(url) for n in AYAKKABI_DISI)


def _score(product: dict, attrs: dict) -> int:
    hay = fold(" ".join(str(product.get(k, "")) for k in ("ad", "marka", "url")))
    if not _coherent(hay, attrs):
        return -1  # ele
    score = 0
    for key in ("kategori", "renk", "cinsiyet", "model", "beden"):
        val = attrs.get(key)
        if val and fold(str(val)) in hay:
            score += 1
    return score


def match(products: list[dict], attrs: dict) -> list[dict]:
    scored = [{**p, "_skor": _score(p, attrs)} for p in products]
    scored = [p for p in scored if p["_skor"] >= 0]  # tutarsızları at
    scored.sort(key=lambda x: x["_skor"], reverse=True)
    return scored


if __name__ == "__main__":
    demo_products = [
        {"ad": "Erkek Beyaz Spor Ayakkabı 42", "marka": "X", "fiyat": "1299", "url": "u1"},
        {"ad": "Beyaz Erkek Spor Çorap 42", "marka": "Y", "fiyat": "99", "url": "u2"},
        {"ad": "Kadın Siyah Bot", "marka": "Z", "fiyat": "899", "url": "u3"},
    ]
    demo_attrs = {"kategori": "spor ayakkabı", "renk": "beyaz", "cinsiyet": "erkek", "beden": "42"}
    import json
    print(json.dumps(match(demo_products, demo_attrs), ensure_ascii=False, indent=2))
