# 🛒 Türkiye E-Ticaret Meta Arama (Demo)

Doğal dilde ürün ararsın ("beyaz erkek spor ayakkabı, beden 42"), sistem birkaç Türk
e-ticaret sitesinden eşleşen ürünlerin **site + link + fiyat**ını getirir.
Kişisel portföy/demo — **ticari servis değildir**, 0 bütçe.

## Nasıl çalışır (5 katman)
1. **Anlama** — sorguyu `{kategori, renk, cinsiyet, model, beden}`'e çevirir.
2. **Keşif** — Google Programmable Search (site-whitelist) ile ürün URL'leri bulur.
3. **Çıkarım** — ürün sayfasındaki **JSON-LD (schema.org)** verisini parse eder (fiyat, ad, marka…). Yoksa CSS fallback.
4. **Eşleştirme** — sonuçları istenen özelliklere göre süzer/puanlar.
5. **Sunum** — statik site `data.json`'u okuyup listeler.

## Hosting modeli
Toplayıcı **senin bilgisayarında** (ev IP'si) koşar → `data.json` üretir → repoya push →
**GitHub Pages** siteyi + veriyi ücretsiz yayınlar. Böylece bulut/anti-bot maliyeti yok.

## Kurulum
```bash
winget install Python.Python.3.12        # Python yoksa
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env                    # GOOGLE_API_KEY, GOOGLE_CSE_ID doldur
```

## Kullanım
```bash
# Tek ürün çıkarımı (anahtar gerektirmez):
venv\Scripts\python backend\extract.py "https://www.trendyol.com/.../p-123456"

# Site temizlik raporu:
venv\Scripts\python backend\probe.py

# Uçtan uca (Google anahtarları gerekir): sorgu → data/data.json
venv\Scripts\python backend\build_data.py "beyaz erkek spor ayakkabı beden 42"

# Siteyi lokalde gör:
#   site/ klasörünü bir statik sunucuyla aç (ör. VS Code Live Server)
```

## Kısıtlar / etik
Yalnızca herkese açık ürün sayfaları okunur, **robots.txt**'ye saygı gösterilir, hız
düşük tutulur ve sonuçlar cache'lenir. Kimlik doğrulaması gereken hiçbir adım
otomatikleştirilmez.

## Durum
Erken iskelet. Ayrıntı ve yol haritası için **CLAUDE.md**'ye bakın.
