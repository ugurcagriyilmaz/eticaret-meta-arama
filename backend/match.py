"""
K4 — Eşleştirme (Matching)  [YER TUTUCU]
Çıkarılan ürünleri, istenen attribute'lara göre filtreler/puanlar.
Şimdilik basit kural + yer tutucu; ileride LLM ile değişecek (imza sabit).

    match(products: list[dict], attrs: dict) -> list[dict]  # skorla sıralı
"""
from __future__ import annotations


def _score(product: dict, attrs: dict) -> int:
    """İstenen attribute'lar ürün metninde geçiyor mu? Kaba metin eşleşmesi."""
    hay = " ".join(
        str(product.get(k, "")) for k in ("ad", "marka", "url")
    ).lower()
    score = 0
    for key in ("kategori", "renk", "cinsiyet", "model", "beden"):
        val = attrs.get(key)
        if val and str(val).lower() in hay:
            score += 1
    return score


def match(products: list[dict], attrs: dict) -> list[dict]:
    scored = []
    for p in products:
        s = _score(p, attrs)
        p = {**p, "_skor": s}
        scored.append(p)
    # skoru olanları öne al; skor 0 olsa bile at (demo için) — ama sırala
    scored.sort(key=lambda x: x["_skor"], reverse=True)
    return scored


if __name__ == "__main__":
    demo_products = [
        {"ad": "Erkek Beyaz Spor Ayakkabı 42", "marka": "X", "fiyat": "1299", "url": "u1"},
        {"ad": "Kadın Siyah Bot", "marka": "Y", "fiyat": "899", "url": "u2"},
    ]
    demo_attrs = {"kategori": "spor ayakkabı", "renk": "beyaz", "cinsiyet": "erkek", "beden": "42"}
    import json
    print(json.dumps(match(demo_products, demo_attrs), ensure_ascii=False, indent=2))
