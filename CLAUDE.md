# CLAUDE.md — TR E-Ticaret Meta Arama

## Proje özeti
Türkiye e-ticaret **meta-arama motoru** (portföy/demo, 0 bütçe). Kullanıcı doğal dilde
"beyaz erkek spor ayakkabı, model X, beden 42" der; sistem birkaç Türk e-ticaret
sitesinden eşleşen ürünlerin **site + link + fiyat**ını getirir. Ticari servis değil.

## Mimari (5 katman)
1. **Anlama (K1)** — `backend/understand.py` — NL sorgu → `{kategori, renk, cinsiyet, model, beden}`. *Şimdilik kural-tabanlı yer tutucu; ileride LLM.*
2. **Keşif (K2)** — `backend/search.py` — **Playwright + gerçek Chromium (`headless=False`)** ile her whitelist sitesinin KENDİ arama sayfasını açar, JS render'ı bekler, DOM'daki ürün linklerini toplar. **Google API YOK.** (Not: Hepsiburada Akamai-tarzı güvenlik duvarı nedeniyle görünür tarayıcı ister; toplayıcı lokalde koştuğu için sorun değil.)
3. **Çıkarım (K3)** — `backend/extract.py` — ürün sayfası → JSON-LD (schema.org Product/Offer) parse → `{ad, fiyat, para_birimi, marka, gorsel, stok, url}`. JSON-LD yoksa CSS/meta fallback. **Gerçek çalışır.**
4. **Eşleştirme (K4)** — `backend/match.py` — sonuçları attribute'lara göre filtrele/puanla. *Basit kural yer tutucu; ileride LLM.*
5. **Sunum (K5)** — `site/index.html + app.js + style.css` — `data.json`'u fetch edip listeler.

`backend/build_data.py` boru hattını (K1→K2→K3→K4) birleştirir ve `data/data.json` üretir.
Aramaya attribute'lardan temiz sorgu kurar, geniş aday havuzu çeker, kategoriye göre
ön-eler (`slug_ok`), siteler arası **round-robin** dengeler, robots.txt'ye saygı gösterir.

## Hosting modeli
Veri toplayıcı **LOKALDE** koşar (ev IP'si, anti-bot toleransı), `data.json` üretir,
repoya push'lar. **GitHub Pages** statik siteyi + `data.json`'u ücretsiz sunar.
`scripts/run_daily.bat` = build + git push tetikleyicisi (Task Scheduler ile gece).

## Kısıtlar (uyulacak)
- Yalnızca **herkese açık** ürün sayfaları; **robots.txt**'ye saygı (build_data.py kontrol eder).
- Düşük hız (varsayılan 2 sn gecikme), küçük ölçek, sonuçları **cache**'le (`data/cache/`).
- Kimlik doğrulaması gereken hiçbir şeyi otomatik geçme.

## Dizin haritası
```
backend/  understand.py(K1) search.py(K2) extract.py(K3) match.py(K4) build_data.py probe.py
site/     index.html app.js style.css
data/     data.json (+ cache/)
scripts/  run_daily.bat
.env.example  requirements.txt  CLAUDE.md  .cursorrules  README.md
```

## Kurulum
```
winget install Python.Python.3.12          # Python yoksa
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m playwright install chromium   # K2 için tarayıcı
```
Harici arama API'si / anahtar YOK — `.env` gerekmiyor.
Test: `venv\Scripts\python backend\extract.py <urun_url>` (çıkarım)
      `venv\Scripts\python backend\search.py "beyaz erkek spor ayakkabı"` (keşif)
      `venv\Scripts\python backend\build_data.py "..." --limit 9` (uçtan uca)

## Kimlik / hesaplar (Part B)
- **GitHub** — **public** repo + Pages (GitHub Actions ile /site + data.json yayını). ✅
- ~~Google Cloud / Programmable Search~~ — **KULLANILMIYOR.** Custom Search JSON API
  yeni müşterilere kapalı; K2 doğrudan Playwright ile yapılıyor. (Proje + API key + PSE
  temizlendi, iz bırakılmadı.)
- **Jira (free)** — "E-ticaret Meta-Arama" board (Gün 1/2/3). *(beklemede)*
- **Cursor** — geliştirme editörü. *(beklemede)*
E-posta: `ugur.cagri.yilmaz@gmail.com`. Harici anahtar yok.

## SIRADAKI ADIMLAR
- [x] Python kurulumu + venv + `pip install -r requirements.txt`.
- [x] `extract.py`'yi gerçek bir Trendyol/Hepsiburada ürün URL'i ile doğrula.
- [x] GitHub public repo + push + Pages (Actions ile /site + data.json).
- [x] K2 keşif: Playwright ile 3 site (Trendyol/HB/n11) — Google'sız çalışıyor.
- [x] `build_data.py` uçtan uca: gerçek, kategori-tutarlı, site-dengeli `data.json`.
- [ ] K1 (understand) ve K4 (match) yer tutucularını LLM ile değiştir.
- [ ] Jira board + Cursor kurulumları.
- [ ] `run_daily.bat` + Windows Task Scheduler ile gecelik otomatik toplama.
