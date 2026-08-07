"""
K4 — Eşleştirme (Matching)  [LLM + kural fallback]
Çıkarılan ürünleri, istenen attribute'lara göre filtreler/puanlar.

    match(products, attrs) -> list[dict]   # alaka skoruyla sıralı (0..3)
    slug_ok(url, attrs) -> bool            # çıkarımdan ÖNCE ucuz URL ön-elemesi (kural)

Ana yol: **Claude (LLM)** tek çağrıda tüm ürünleri semantik alaka için puanlar
(kategori uyumu + renk/cinsiyet/beden). Anahtar yoksa/çağrı düşerse kural-tabanlı
`_rule_match`'e düşer. slug_ok her zaman kuraldır (indirmeden önce çalışır, ucuz olmalı).
"""
from __future__ import annotations

import json

import llm
from understand import fold

# --- Kural fallback için kökler ---
AYAKKABI = ("ayakkabi", "sneaker", "bot")
AYAKKABI_DISI = (
    "corap", "socks", "sapka", "bere", "atki", "eldiven", "sweatshirt",
    "tisort", "t-shirt", "forma", "kemer", "canta", "sort", "hoodie",
    "bileklik", "kolye", "mont", "esofman",
)


def _footwear_query(attrs: dict) -> bool:
    kat = fold(str(attrs.get("kategori") or ""))
    return any(f in kat for f in AYAKKABI)


def _coherent(hay: str, attrs: dict) -> bool:
    if not _footwear_query(attrs):
        return True
    if any(n in hay for n in AYAKKABI_DISI):
        return False
    return any(f in hay for f in AYAKKABI)


def slug_ok(url: str, attrs: dict) -> bool:
    """Çıkarımdan ÖNCE ucuz eleme: yalnızca AÇIKÇA alakasız slug'ları at (çorap/şapka).
    Pozitif kök zorunlu değil (marka-adı slug'lı ayakkabılar elenmesin). KURAL — hızlı."""
    if not _footwear_query(attrs):
        return True
    return not any(n in fold(url) for n in AYAKKABI_DISI)


# ---------------- Kural fallback ----------------
def _rule_score(product: dict, attrs: dict) -> int:
    hay = fold(" ".join(str(product.get(k, "")) for k in ("ad", "marka", "url")))
    if not _coherent(hay, attrs):
        return -1
    score = 0
    for key in ("kategori", "renk", "cinsiyet", "model", "beden"):
        val = attrs.get(key)
        if val and fold(str(val)) in hay:
            score += 1
    return score


def _rule_match(products: list[dict], attrs: dict) -> list[dict]:
    scored = [{**p, "_skor": _rule_score(p, attrs)} for p in products]
    scored = [p for p in scored if p["_skor"] >= 0]
    scored.sort(key=lambda x: x["_skor"], reverse=True)
    return scored


# ---------------- LLM ana yol ----------------
_SCHEMA_MATCH = {
    "type": "object", "additionalProperties": False, "required": ["sonuclar"],
    "properties": {"sonuclar": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["i", "skor", "uygun"],
        "properties": {
            "i": {"type": "integer"},
            "skor": {"type": "integer"},
            "uygun": {"type": "boolean"},
        }}}},
}


def _llm_match(products: list[dict], attrs: dict) -> list[dict] | None:
    if not products:
        return []
    if not llm.key_available():
        return None
    istek = {k: attrs.get(k) for k in ("kategori", "renk", "cinsiyet", "model", "beden")
             if attrs.get(k)}
    liste = "\n".join(f"{i}. {p.get('ad') or '(adsız)'}" for i, p in enumerate(products))
    prompt = f"""Kullanıcının istediği ürün özellikleri (JSON):
{json.dumps(istek, ensure_ascii=False)}

Aşağıdaki ürünleri bu isteğe göre değerlendir. Her ürün için:
- skor: 0-3 (3 = özellikler tam uyuyor, 0 = alakasız). Renk/cinsiyet/kategori uyumuna bak.
- uygun: kategori uyuyorsa true. AÇIKÇA farklı kategori ise false (ör. ayakkabı istenip
  çorap/şapka/sweatshirt gelmişse false).

Ürünler:
{liste}

Her ürün için {{i, skor, uygun}} döndür (tüm indeksler için)."""
    data = llm.structured(prompt, _SCHEMA_MATCH, max_tokens=1200)
    if not data or "sonuclar" not in data:
        return None
    by_i = {r["i"]: r for r in data["sonuclar"] if isinstance(r.get("i"), int)}
    out = []
    for i, p in enumerate(products):
        r = by_i.get(i)
        if r is None:            # LLM atladıysa: düşük skorla tut (sessizce silme)
            out.append({**p, "_skor": 0})
            continue
        if not r.get("uygun", True):
            continue             # açıkça farklı kategori → ele
        out.append({**p, "_skor": max(0, min(3, int(r.get("skor", 0))))})
    out.sort(key=lambda x: x["_skor"], reverse=True)
    return out


def match(products: list[dict], attrs: dict) -> list[dict]:
    res = _llm_match(products, attrs)
    if res is not None:
        return res
    return _rule_match(products, attrs)


if __name__ == "__main__":
    demo = [
        {"ad": "Erkek Beyaz Spor Ayakkabı 42", "marka": "X", "url": "u1"},
        {"ad": "Beyaz Erkek Spor Çorap 42", "marka": "Y", "url": "u2"},
        {"ad": "Kadın Siyah Bot", "marka": "Z", "url": "u3"},
    ]
    attrs = {"kategori": "spor ayakkabı", "renk": "beyaz", "cinsiyet": "erkek", "beden": "42"}
    print(json.dumps(match(demo, attrs), ensure_ascii=False, indent=2))
