"""
backfill_jira.py — Mevcut EMA issue'larının BOŞ açıklamalarını Claude ile,
docs/jira-format.md formatında doldurur.
  - Epic  -> Amaç / Kapsam / Kapsam dışı / DoD
  - Diğer -> Ne / Neden / Kabul kriterleri
Zaten açıklaması olanları atlar (idempotent). Anahtarlar .anthropic_key/.jira_token.

Kullanım:
    python scripts/backfill_jira.py --dry-run --limit 2   # önizleme
    python scripts/backfill_jira.py                       # hepsini doldur
"""
from __future__ import annotations
import sys, json, base64, urllib.request, urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SITE = "https://ugurcagriyilmaz.atlassian.net"
EMAIL = "ugur.cagri.yilmaz@gmail.com"
MODEL = "claude-haiku-4-5"   # daha zengin: "claude-opus-5"

PROJE = ("Türkiye e-ticaret meta-arama motoru (portföy/demo). Kullanıcı doğal dilde ürün arar; "
         "3 siteden (Trendyol/Hepsiburada/n11) fiyat+link+görsel toplanır. Python backend "
         "(understand->search->extract->match->build_data) + statik site (GitHub Pages). "
         "Playwright ile keşif, curl_cffi ile fetch, JSON-LD ile çıkarım. Ticari değil, 0 bütçe.")


def jira(method, path, body=None):
    tok = (ROOT / ".jira_token").read_text(encoding="utf-8").strip()
    auth = "Basic " + base64.b64encode(f"{EMAIL}:{tok}".encode()).decode()
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(SITE + path, data=data, method=method)
    r.add_header("Authorization", auth); r.add_header("Accept", "application/json")
    if data: r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            t = x.read().decode(); return x.status, (json.loads(t) if t else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:200]}


def _p(t): return {"type": "paragraph", "content": [{"type": "text", "text": t}]}
def _bullets(items): return {"type": "bulletList",
    "content": [{"type": "listItem", "content": [_p(i)]} for i in (items or ["-"])]}


def adf_task(d):
    return {"type": "doc", "version": 1, "content": [
        _p(f"Ne: {d['ne']}"), _p(f"Neden: {d['neden']}"),
        _p("Kabul kriterleri:"), _bullets(d["kabul"])]}


def adf_epic(d):
    return {"type": "doc", "version": 1, "content": [
        _p(f"Amaç: {d['amac']}"), _p("Kapsam:"), _bullets(d["kapsam"]),
        _p(f"Kapsam dışı: {d['kapsam_disi']}"), _p(f"DoD: {d['dod']}")]}


SCHEMA_TASK = {"type": "object", "additionalProperties": False,
    "required": ["ne", "neden", "kabul"], "properties": {
        "ne": {"type": "string"}, "neden": {"type": "string"},
        "kabul": {"type": "array", "items": {"type": "string"}}}}
SCHEMA_EPIC = {"type": "object", "additionalProperties": False,
    "required": ["amac", "kapsam", "kapsam_disi", "dod"], "properties": {
        "amac": {"type": "string"}, "kapsam": {"type": "array", "items": {"type": "string"}},
        "kapsam_disi": {"type": "string"}, "dod": {"type": "string"}}}


def gen(client, summary, itype, component):
    is_epic = itype == "Epic"
    schema = SCHEMA_EPIC if is_epic else SCHEMA_TASK
    if is_epic:
        istek = ("Bu bir EPIC. Şunları üret: amac (bu epic neyi çözüyor/kime değer), "
                 "kapsam (2-4 madde, neler dahil), kapsam_disi (neler girmiyor), "
                 "dod (ne zaman biter).")
    else:
        istek = ("Bu bir Story/Task/Bug/Spike. Şunları üret: ne (işin net tanımı), "
                 "neden (neden gerekli/bağlam), kabul (2-4 somut kabul kriteri).")
    prompt = (f"Proje: {PROJE}\n\nJira issue:\n  Özet: {summary}\n  Tip: {itype}\n"
              f"  Component: {component}\n\n{istek}\nTÜRKÇE yaz, kısa ve somut ol.")
    r = client.messages.create(model=MODEL, max_tokens=1200,
        output_config={"format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": prompt}])
    return json.loads(next(b.text for b in r.content if b.type == "text"))


def has_desc(f):
    d = f.get("description")
    return bool(d and d.get("content"))


def main():
    dry = "--dry-run" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    import anthropic
    client = anthropic.Anthropic(api_key=(ROOT / ".anthropic_key").read_text(encoding="utf-8").strip())

    st, res = jira("GET", "/rest/api/3/search/jql?jql=project=EMA%20ORDER%20BY%20created%20ASC"
                          "&fields=summary,issuetype,components,description&maxResults=100")
    issues = res.get("issues", [])
    done = 0
    for it in issues:
        f = it["fields"]; key = it["key"]
        if has_desc(f):
            continue  # zaten dolu
        itype = f["issuetype"]["name"]
        comp = (f.get("components") or [{}])[0].get("name", "-")
        summ = f["summary"]
        d = gen(client, summ, itype, comp)
        adf = adf_epic(d) if itype == "Epic" else adf_task(d)
        print(f"\n{key} [{itype}] {summ[:50]}")
        if itype == "Epic":
            print("   amaç:", d["amac"][:70])
        else:
            print("   ne:", d["ne"][:70])
        if not dry:
            s, _ = jira("PUT", f"/rest/api/3/issue/{key}", {"fields": {"description": adf}})
            print("   ->", "yazıldı" if s in (200, 204) else f"HATA {s}")
        done += 1
        if limit and done >= limit:
            break
    print(f"\n{'[dry] ' if dry else ''}{done} issue işlendi.")


if __name__ == "__main__":
    main()
