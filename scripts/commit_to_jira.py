"""
commit_to_jira.py — Son commit'i Claude'a verip iyi yapılandırılmış Jira issue üretir.
post-commit git hook'undan otomatik çağrılır. Anahtarlar .anthropic_key / .jira_token'dan
okunur (asla yazdırılmaz). Format: docs/jira-format.md.

Kullanım:
    python scripts/commit_to_jira.py            # gerçek: Jira'ya yazar
    python scripts/commit_to_jira.py --dry-run  # sadece üretir, Jira'ya dokunmaz

Kurallar:
- Commit mesajında "EMA-<n>" varsa: o issue'yu TARGET_STATUS'e taşır + yorum ekler (yeni açmaz).
- Mesajda "[skip-jira]" varsa veya merge commit'iyse atlar.
"""
from __future__ import annotations
import sys, re, json, base64, subprocess, urllib.request, urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://ugurcagriyilmaz.atlassian.net"
EMAIL = "ugur.cagri.yilmaz@gmail.com"
PROJECT = "EMA"
MODEL = "claude-haiku-4-5"       # ucuz+hızlı; daha zengin açıklama için: "claude-opus-5"
TARGET_STATUS = "Done"           # commit = biten iş → hangi kolona
COMP = {"Backend": "10000", "Frontend": "10001", "Infra/DevOps": "10002"}
EPICS = {
    "EMA-1": "Çekirdek Meta-Arama (understand/search/extract/match/present pipeline)",
    "EMA-2": "Veri Kalitesi & Çıkarım (fiyat/görsel/doğruluk, anti-bot, kategori filtresi)",
    "EMA-3": "Altyapı & CI/CD (GitHub Pages, Actions, run_daily, deploy, otomasyon)",
    "EMA-4": "Teknik Borç (LLM'e geçiş, dayanıklılık, refactor, tech-debt)",
}


def sh(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8").strip()


def jira(method: str, path: str, body=None):
    tok = (ROOT / ".jira_token").read_text(encoding="utf-8").strip()
    auth = "Basic " + base64.b64encode(f"{EMAIL}:{tok}".encode()).decode()
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(SITE + path, data=data, method=method)
    r.add_header("Authorization", auth)
    r.add_header("Accept", "application/json")
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            t = x.read().decode()
            return x.status, (json.loads(t) if t else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def _para(t): return {"type": "paragraph", "content": [{"type": "text", "text": t}]}


def adf(ne: str, neden: str, kabul: list[str]):
    """Jira v3 açıklaması ADF formatında olmalı — Ne/Neden + kabul kriterleri listesi."""
    c = [_para(f"Ne: {ne}"), _para(f"Neden: {neden}"), _para("Kabul kriterleri:")]
    c.append({"type": "bulletList",
              "content": [{"type": "listItem", "content": [_para(k)]} for k in (kabul or ["-"])]})
    return {"type": "doc", "version": 1, "content": c}


SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["summary", "type", "component", "epic", "labels", "ne", "neden", "kabul"],
    "properties": {
        "summary": {"type": "string", "description": "Fiil ile başla, kısa ve net"},
        "type": {"type": "string", "enum": ["Story", "Task", "Bug", "Spike"]},
        "component": {"type": "string", "enum": ["Backend", "Frontend", "Infra/DevOps"]},
        "epic": {"type": "string", "enum": list(EPICS)},
        "labels": {"type": "array", "items": {"type": "string", "enum": ["tech-debt", "research", "urgent"]}},
        "ne": {"type": "string"},
        "neden": {"type": "string"},
        "kabul": {"type": "array", "items": {"type": "string"}},
    },
}


def classify(msg: str, files: str):
    import anthropic
    key = (ROOT / ".anthropic_key").read_text(encoding="utf-8").strip()
    client = anthropic.Anthropic(api_key=key)
    epics = "\n".join(f"  {k}: {v}" for k, v in EPICS.items())
    prompt = f"""Bir git commit'ini iyi yapılandırılmış bir Jira issue'suna çevir. TÜRKÇE yaz, docs/jira-format.md formatına uy.

COMMIT MESAJI:
{msg}

DEĞİŞEN DOSYALAR:
{files or '(bilinmiyor)'}

KURALLAR:
- summary: fiil ile başla (ekle/düzelt/kur...), kısa ve net.
- type: fix->Bug, feat->Story, araştırma/PoC->Spike, diğeri->Task.
- component: backend/*.py -> Backend, site/* -> Frontend, .github|scripts|deploy|run_daily -> Infra/DevOps.
- epic: aşağıdakilerden EN UYGUN olanın anahtarını seç:
{epics}
- labels: uygunsa tech-debt/research/urgent; değilse boş dizi.
- ne: yapılan işin net tanımı. neden: neden gerekliydi (bağlam).
- kabul: 2-4 somut kabul kriteri (commit'ten çıkarabildiğin kadar)."""
    r = client.messages.create(
        model=MODEL, max_tokens=1500,
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    )
    txt = next(b.text for b in r.content if b.type == "text")
    return json.loads(txt), r.usage


def move_to(key: str, target: str) -> bool:
    _, d = jira("GET", f"/rest/api/3/issue/{key}/transitions")
    for t in d.get("transitions", []):
        if (t.get("to", {}) or {}).get("name", "") == target:
            jira("POST", f"/rest/api/3/issue/{key}/transitions", {"transition": {"id": t["id"]}})
            return True
    return False


def main() -> int:
    dry = "--dry-run" in sys.argv
    msg = sh("git", "log", "-1", "--pretty=%B")
    subj = msg.splitlines()[0] if msg else ""
    sha = sh("git", "log", "-1", "--pretty=%h")

    if "[skip-jira]" in msg.lower():
        print("[skip-jira] — atlandı")
        return 0
    if subj.lower().startswith("merge"):
        print("merge commit — atlandı")
        return 0

    files = sh("git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")

    # Mesajda var olan bir issue anahtarı referans mı?
    m = re.search(r"\bEMA-\d+\b", msg)
    if m:
        key = m.group(0)
        print(f"Referans bulundu: {key} → {TARGET_STATUS}")
        if not dry:
            move_to(key, TARGET_STATUS)
            jira("POST", f"/rest/api/3/issue/{key}/comment",
                 {"body": {"type": "doc", "version": 1, "content": [_para(f"commit {sha}: {subj}")]}})
        print(f"{'[dry] ' if dry else ''}{key} güncellendi + yorum eklendi.")
        return 0

    data, usage = classify(msg, files)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"token: {usage.input_tokens} girdi / {usage.output_tokens} çıktı")
    if dry:
        print("[dry-run] Jira'ya YAZILMADI.")
        return 0

    fields = {
        "project": {"key": PROJECT}, "summary": data["summary"],
        "issuetype": {"name": data["type"]}, "parent": {"key": data["epic"]},
        "components": [{"id": COMP[data["component"]]}], "labels": data.get("labels") or [],
        "description": adf(data["ne"], data["neden"], data["kabul"]),
    }
    st, d = jira("POST", "/rest/api/3/issue", {"fields": fields})
    key = d.get("key")
    if not key:
        print("HATA oluştur:", st, d.get("error", "")[:200])
        return 1
    move_to(key, TARGET_STATUS)
    print(f"OLUŞTURULDU: {key} [{data['type']}/{data['component']}/{TARGET_STATUS}] {data['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
