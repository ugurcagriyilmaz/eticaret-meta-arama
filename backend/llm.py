"""
Ortak LLM yardımcısı — Claude ile yapılandırılmış (JSON-schema) çağrı.

Tasarım ilkesi: **LLM ana yol, kural fallback.** Anahtar (.anthropic_key) yoksa ya da
çağrı düşerse `structured()` None döner; çağıran modül (understand/match) kural-tabanlı
yönteme düşer. Böylece anahtarsız/çevrimdışı ortamda sistem yine çalışır.

Aynı gün içinde aynı prompt+schema → disk cache (data/cache/llm/); tekrar token harcanmaz.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = "claude-haiku-4-5"   # ucuz+hızlı; daha güçlü anlama için: "claude-opus-5"
LLM_CACHE = ROOT / "data" / "cache" / "llm"
LLM_CACHE.mkdir(parents=True, exist_ok=True)


def key_available() -> bool:
    p = ROOT / ".anthropic_key"
    return p.exists() and bool(p.read_text(encoding="utf-8").strip())


def _key() -> str | None:
    p = ROOT / ".anthropic_key"
    if not p.exists():
        return None
    k = p.read_text(encoding="utf-8").strip()
    return k or None


def _cache_path(prompt: str, schema: dict, max_tokens: int) -> Path:
    today = datetime.now().astimezone().date().isoformat()
    blob = f"{today}\n{max_tokens}\n{prompt}\n{json.dumps(schema, sort_keys=True)}"
    key = hashlib.sha256(blob.encode()).hexdigest()[:16]
    return LLM_CACHE / f"{key}.json"


def structured(prompt: str, schema: dict, max_tokens: int = 800) -> dict | None:
    """Claude'dan `schema`ya uygun JSON al. Anahtar yoksa/çağrı düşerse None."""
    key = _key()
    if not key:
        return None
    cf = _cache_path(prompt, schema, max_tokens)
    if cf.exists():
        try:
            return json.loads(cf.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - bozuk cache → yeniden çağır
            cf.unlink(missing_ok=True)
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key, timeout=30.0, max_retries=1)
        r = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            output_config={"format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": prompt}],
        )
        txt = next(b.text for b in r.content if b.type == "text")
        data = json.loads(txt)
        cf.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data
    except Exception as e:  # noqa: BLE001 - LLM düşerse sessizce kural fallback
        print(f"[llm] düştü → kural fallback: {str(e)[:90]}")
        return None
