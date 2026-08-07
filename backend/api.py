"""
api.py — Canlı arama HTTP API'si (FastAPI).
GET /search?q=...&limit=6  → pipeline'ı (understand→search→extract→match) O AN çalıştırır,
data.json ile aynı yapıda JSON döner. Statik site bu endpoint'i çağırır.

Çalıştırma (repo kökünden):
    venv\\Scripts\\python.exe -m uvicorn backend.api:app --host 0.0.0.0 --port 8000

Not: Pipeline Playwright + curl_cffi + LLM kullanır → LOKAL/ev-IP'de koşmalı (anti-bot).
Public erişim için Cloudflare Tunnel ile bu porta tünel açılır.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# backend/ dizinini path'e ekle (build_data ve bağımlılıkları oradan import edilir)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_data import build  # noqa: E402

app = FastAPI(title="TR E-Ticaret Meta Arama API")

# Statik site (GitHub Pages) tarayıcıdan çağırabilsin diye CORS açık.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"ok": True, "kullanim": "/search?q=beyaz erkek spor ayakkabı&limit=6"}


@app.get("/saglik")
def saglik():
    return {"ok": True}


# `def` (async değil) → FastAPI thread-pool'da çalıştırır; sync Playwright sorunsuz.
@app.get("/search")
def search(q: str = Query(..., min_length=2, max_length=120),
           limit: int = Query(6, ge=1, le=12)):
    # Canlı arama: düşük gecikme (nazik ama hızlı)
    return build(q, limit=limit, delay=0.6)
