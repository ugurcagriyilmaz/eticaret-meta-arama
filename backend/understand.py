"""
K1 — Anlama (Understanding)  [YER TUTUCU]
Doğal dil sorgusunu yapılandırılmış attribute'lara çevirir:
    {kategori, renk, cinsiyet, model, beden}

Şimdilik basit kural-tabanlı bir yer tutucu. İleride bir LLM çağrısıyla değişecek
(imza aynı kalacak: understand(query: str) -> dict).
"""
from __future__ import annotations

import re
import sys
import json

# Türkçe karakterleri ASCII'ye katla (ı/ş/ç/ğ/ü/ö → i/s/c/g/u/o) — kullanıcı
# "ayakkabi" da yazsa "ayakkabı" da tutsun. Diğer modüller de bunu kullanır.
_TR = str.maketrans("ıİşŞçÇğĞüÜöÖ", "iissccgguuoo")


def fold(s: str) -> str:
    return (s or "").translate(_TR).casefold()


RENKLER = {
    "beyaz", "siyah", "kırmızı", "mavi", "yeşil", "sarı", "gri", "pembe",
    "mor", "turuncu", "kahverengi", "lacivert", "bej", "bordo",
}
CINSIYET = {
    "erkek": "erkek", "kadın": "kadın", "kadin": "kadın",
    "unisex": "unisex", "çocuk": "çocuk", "cocuk": "çocuk",
}
KATEGORILER = {
    "spor ayakkabı", "sneaker", "ayakkabı", "bot", "tişört", "tshirt",
    "pantolon", "ceket", "mont", "çanta", "telefon", "laptop", "kulaklık",
}


def understand(query: str) -> dict:
    q = fold(query)  # Türkçe-normalize (ayakkabı ↔ ayakkabi)
    renk = next((r for r in RENKLER if fold(r) in q), None)
    cinsiyet = next((v for k, v in CINSIYET.items() if fold(k) in q), None)
    kategori = next(
        (k for k in sorted(KATEGORILER, key=len, reverse=True) if fold(k) in q), None
    )
    # beden: "beden 42", "42 numara", "boyu M"
    beden = None
    m = re.search(r"\b(beden|numara|no)\s*[:\-]?\s*(\d{2}|[sml]|xl|xxl)\b", q)
    if m:
        beden = m.group(2).upper()
    else:
        m = re.search(r"\b(3[5-9]|4[0-6])\b", q)  # ayakkabı numarası aralığı
        if m:
            beden = m.group(1)
    # model: tırnak içi veya "model X"
    model = None
    m = re.search(r'"([^"]+)"', query) or re.search(r"\bmodel\s+([\w\- ]{2,30})", q)
    if m:
        model = m.group(1).strip()
    return {
        "kategori": kategori,
        "renk": renk,
        "cinsiyet": cinsiyet,
        "model": model,
        "beden": beden,
        "_ham_sorgu": query,
    }


def main() -> int:
    q = " ".join(sys.argv[1:]) or "beyaz erkek spor ayakkabı model X beden 42"
    print(json.dumps(understand(q), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
