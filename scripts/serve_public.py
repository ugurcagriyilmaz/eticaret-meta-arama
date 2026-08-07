"""
serve_public.py — Canlı arama sunucusunu PUBLIC yapar (tek komut).

  1) FastAPI API'yi başlatır (uvicorn, :8000)
  2) Cloudflare Tunnel açar → geçici public URL alır
  3) URL'i site/api.json'a yazar, commit + push eder (Pages ~1 dk sonra kullanır)
  4) Ctrl+C'ye kadar açık kalır; kapanınca ikisini de durdurur

Kullanım (repo kökünden):
    venv\\Scripts\\python.exe scripts\\serve_public.py

NOT: Tünel URL'i her açılışta DEĞİŞİR (trycloudflare). Bu script her seferinde
yeni URL'i push'ladığı için public site otomatik güncellenir. Makinen açık +
internet + bu script çalışırken canlı arama herkese açıktır; kapanınca statik
site (hazır sonuçlar) yine görünür.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = str(ROOT / "venv" / "Scripts" / "python.exe")
CF = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
TUN_LOG = ROOT / "scripts" / "tunnel.log"
PAGES = "https://ugurcagriyilmaz.github.io/eticaret-meta-arama/"


def main() -> int:
    if not Path(CF).exists():
        print(f"cloudflared bulunamadı: {CF}\n(winget install Cloudflare.cloudflared)")
        return 1

    print("[1/4] API başlatılıyor (uvicorn :8000)…")
    api = subprocess.Popen(
        [PY, "-m", "uvicorn", "backend.api:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT,
    )
    time.sleep(4)

    print("[2/4] Cloudflare Tunnel açılıyor…")
    logf = open(TUN_LOG, "w", encoding="utf-8")
    tun = subprocess.Popen(
        [CF, "tunnel", "--url", "http://localhost:8000"],
        cwd=ROOT, stdout=logf, stderr=subprocess.STDOUT,
    )

    url = None
    for _ in range(40):
        time.sleep(1)
        try:
            txt = TUN_LOG.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            txt = ""
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", txt)
        if m:
            url = m.group(0)
            break

    if not url:
        print("Tünel URL'i alınamadı. tunnel.log'a bakın.")
        tun.terminate(); api.terminate()
        return 1

    print(f"[3/4] Public URL: {url}  → api.json'a yazılıyor + push…")
    (ROOT / "site" / "api.json").write_text(
        json.dumps({"api": url, "not": "Cloudflare Tunnel (geçici URL) -> localhost:8000"},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "site/api.json"], cwd=ROOT)
    subprocess.run(["git", "commit", "-m", "chore: canli arama api url guncelle [skip-jira]"], cwd=ROOT)
    subprocess.run(["git", "push"], cwd=ROOT)

    print("\n" + "=" * 60)
    print("✅ PUBLIC CANLI ARAMA HAZIR")
    print(f"   Site : {PAGES}  (deploy ~1 dk sonra yeni URL'i kullanır)")
    print(f"   API  : {url}")
    print("   Durdurmak için: Ctrl+C")
    print("=" * 60 + "\n")

    try:
        tun.wait()
    except KeyboardInterrupt:
        print("\nKapatılıyor…")
    finally:
        for p in (tun, api):
            try:
                p.terminate()
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
