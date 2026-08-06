# CLAUDE.md — TR E-Ticaret Meta Arama

## Proje özeti
Türkiye e-ticaret **meta-arama motoru** (portföy/demo, 0 bütçe). Kullanıcı doğal dilde
"beyaz erkek spor ayakkabı, model X, beden 42" der; sistem birkaç Türk e-ticaret
sitesinden eşleşen ürünlerin **site + link + fiyat**ını getirir. Ticari servis değil.

## Mimari (5 katman)
1. **Anlama (K1)** — `backend/understand.py` — NL sorgu → `{kategori, renk, cinsiyet, model, beden}`. *Şimdilik kural-tabanlı yer tutucu; ileride LLM.*
2. **Keşif (K2)** — `backend/search.py` — Google Programmable Search JSON API (site-whitelist) → ürün URL'leri.
3. **Çıkarım (K3)** — `backend/extract.py` — ürün sayfası → JSON-LD (schema.org Product/Offer) parse → `{ad, fiyat, para_birimi, marka, gorsel, stok, url}`. JSON-LD yoksa CSS/meta fallback. **Gerçek çalışır.**
4. **Eşleştirme (K4)** — `backend/match.py` — sonuçları attribute'lara göre filtrele/puanla. *Basit kural yer tutucu; ileride LLM.*
5. **Sunum (K5)** — `site/index.html + app.js + style.css` — `data.json`'u fetch edip listeler.

`backend/build_data.py` boru hattını (K1→K2→K3→K4) birleştirir ve `data/data.json` üretir.

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
winget install Python.Python.3.12   # Python yoksa
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env              # GOOGLE_API_KEY / GOOGLE_CSE_ID doldur
```
Test: `venv\Scripts\python backend\extract.py <urun_url>`

## Kimlik / hesaplar (Part B)
- **GitHub** — private repo + Pages (/site).
- **Google Cloud** — Custom Search API etkin, `GOOGLE_API_KEY`.
- **Programmable Search Engine** — whitelist: trendyol/hepsiburada/n11 → `GOOGLE_CSE_ID`.
- **Jira (free)** — "E-ticaret Meta-Arama" board (Gün 1/2/3).
- **Cursor** — geliştirme editörü.
E-posta: `ugur.cagri.yilmaz@gmail.com`. Anahtarlar yalnızca yerel `.env`'de (push yok).

## SIRADAKI ADIMLAR
- [ ] Python kurulumu + venv + `pip install -r requirements.txt`.
- [ ] `extract.py`'yi gerçek bir Trendyol/Hepsiburada ürün URL'i ile doğrula.
- [ ] GitHub private repo + push + Pages (/site) yayınla.
- [ ] Google Cloud Custom Search API key + Programmable Search Engine ID → `.env`.
- [ ] `search.py` ve `build_data.py`'yi gerçek anahtarlarla uçtan uca çalıştır.
- [ ] K1 (understand) ve K4 (match) yer tutucularını LLM ile değiştir.
- [ ] Jira board + Cursor kurulumları.
