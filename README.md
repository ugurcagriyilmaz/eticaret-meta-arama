# 🛒 Türkiye E-Ticaret Meta Arama (Demo)

Doğal dilde ürün ararsın ("beyaz erkek spor ayakkabı, beden 42"), sistem birkaç Türk
e-ticaret sitesinden eşleşen ürünlerin **site + link + fiyat**ını getirir.
Kişisel portföy/demo — **ticari servis değildir**, 0 bütçe.

## Nasıl çalışır (5 katman)
1. **Anlama** — sorguyu `{kategori, renk, cinsiyet, model, beden}`'e çevirir.
2. **Keşif** — **Playwright + gerçek Chromium** ile her sitenin kendi aramasını render edip ürün URL'lerini toplar (harici API/anahtar yok).
3. **Çıkarım** — ürün sayfasındaki **JSON-LD (schema.org)** verisini parse eder (fiyat, ad, marka…). Yoksa CSS fallback.
4. **Eşleştirme** — sonuçları istenen özelliklere göre süzer/puanlar.
5. **Sunum** — statik site `data.json`'u okuyup listeler.

## Hosting modeli
Toplayıcı **senin bilgisayarında** (ev IP'si) koşar → `data.json` üretir → repoya push →
**GitHub Pages** siteyi + veriyi ücretsiz yayınlar. Böylece bulut/anti-bot maliyeti yok.

## Kurulum
```bash
winget install Python.Python.3.12                    # Python yoksa
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m playwright install chromium   # Keşif için tarayıcı
```
Harici arama API'si veya anahtar gerekmez; `.env` yok.

## Kullanım
```bash
# Tek ürün çıkarımı:
venv\Scripts\python backend\extract.py "https://www.trendyol.com/.../p-123456"

# Keşif (Playwright ile 3 siteden ürün linkleri):
venv\Scripts\python backend\search.py "beyaz erkek spor ayakkabı"

# Uçtan uca: sorgu → data/data.json (gerçek, kategori-tutarlı, site-dengeli):
venv\Scripts\python backend\build_data.py "beyaz erkek spor ayakkabı beden 42" --limit 9

# Siteyi lokalde gör:
#   site/ klasörünü bir statik sunucuyla aç (ör. VS Code Live Server)
```

## Kısıtlar / etik
Yalnızca herkese açık ürün sayfaları okunur, **robots.txt**'ye saygı gösterilir, hız
düşük tutulur ve sonuçlar cache'lenir. Kimlik doğrulaması gereken hiçbir adım
otomatikleştirilmez.

## Canlı demo
GitHub Pages: **https://ugurcagriyilmaz.github.io/eticaret-meta-arama/**

## Durum
Uçtan uca çalışıyor: 3 site (Trendyol/Hepsiburada/n11), gerçek veri.
Ayrıntı ve yol haritası için **CLAUDE.md**'ye bakın.
