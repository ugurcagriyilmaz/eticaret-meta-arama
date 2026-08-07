"""
K1 — Anlama (Understanding)  [LLM + kural fallback]
Doğal dil sorgusunu yapılandırılmış attribute'lara çevirir:
    {kategori, renk, cinsiyet, model, beden}

Ana yol: **Claude (LLM)** — sözlükte olmayan renk/kategori/eş anlamlıları da anlar
("bordo süet bot", "42 numara beyaz sneakers", "haki parka"). Anahtar yoksa ya da
çağrı düşerse kural-tabanlı `_rule_understand`'e düşer. İmza sabit: understand(query)->dict.
"""
from __future__ import annotations

import re
import sys
import json

import llm

# Türkçe karakterleri ASCII'ye katla (ı/ş/ç/ğ/ü/ö → i/s/c/g/u/o). Diğer modüller de kullanır.
_TR = str.maketrans("ıİşŞçÇğĞüÜöÖ", "iissccgguuoo")


def fold(s: str) -> str:
    return (s or "").translate(_TR).casefold()


RENKLER = {
    "beyaz", "siyah", "kırmızı", "mavi", "yeşil", "sarı", "gri", "pembe",
    "mor", "turuncu", "kahverengi", "lacivert", "bej", "bordo", "haki", "petrol",
}
CINSIYET = {
    "erkek": "erkek", "kadın": "kadın", "kadin": "kadın",
    "unisex": "unisex", "çocuk": "çocuk", "cocuk": "çocuk",
}
KATEGORILER = {
    "spor ayakkabı", "sneaker", "ayakkabı", "bot", "tişört", "tshirt",
    "pantolon", "ceket", "mont", "çanta", "telefon", "laptop", "kulaklık",
}

_ALANLAR = ("kategori", "renk", "cinsiyet", "model", "beden")

_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": list(_ALANLAR),
    "properties": {a: {"type": "string"} for a in _ALANLAR},
}


def _rule_understand(query: str) -> dict:
    """Kural-tabanlı fallback (sözlük + regex)."""
    q = fold(query)
    renk = next((r for r in RENKLER if fold(r) in q), None)
    cinsiyet = next((v for k, v in CINSIYET.items() if fold(k) in q), None)
    kategori = next(
        (k for k in sorted(KATEGORILER, key=len, reverse=True) if fold(k) in q), None
    )
    beden = None
    m = re.search(r"\b(beden|numara|no)\s*[:\-]?\s*(\d{2}|[sml]|xl|xxl)\b", q)
    if m:
        beden = m.group(2).upper()
    else:
        m = re.search(r"\b(3[5-9]|4[0-6])\b", q)  # ayakkabı numarası aralığı
        if m:
            beden = m.group(1)
    model = None
    m = re.search(r'"([^"]+)"', query) or re.search(r"\bmodel\s+([\w\- ]{2,30})", q)
    if m:
        model = m.group(1).strip()
    return {"kategori": kategori, "renk": renk, "cinsiyet": cinsiyet,
            "model": model, "beden": beden}


def _llm_understand(query: str) -> dict | None:
    prompt = f"""Bir Türkçe ürün arama sorgusundan şu attribute'ları çıkar (JSON):
- kategori: ürün türü (ör. "spor ayakkabı", "bot", "mont", "tişört"). Genel/kanonik ad.
- renk: ana renk (ör. "beyaz", "bordo", "haki"). Türkçe.
- cinsiyet: erkek | kadın | unisex | çocuk
- model: marka/model adı varsa (ör. "Air Max 90"), yoksa boş.
- beden: numara/beden (ör. "42", "M", "XL"), yoksa boş.
BILINMEYEN alanı BOŞ STRING ("") bırak. Uydurma.

Sorgu: {query!r}"""
    data = llm.structured(prompt, _SCHEMA, max_tokens=300)
    if not data:
        return None
    # Boş string'leri None'a çevir, beklenen anahtarları garanti et
    return {a: (str(data.get(a) or "").strip() or None) for a in _ALANLAR}


def understand(query: str) -> dict:
    data = _llm_understand(query)
    kaynak = "llm"
    if data is None:
        data = _rule_understand(query)
        kaynak = "kural"
    data["_ham_sorgu"] = query
    data["_kaynak"] = kaynak
    return data


def main() -> int:
    q = " ".join(sys.argv[1:]) or "beyaz erkek spor ayakkabı model X beden 42"
    print(json.dumps(understand(q), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
