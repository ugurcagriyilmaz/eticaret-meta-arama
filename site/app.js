// K5 — Sunum: hem hazır data.json'u gösterir HEM DE canlı arama yapar.
// Canlı arama, backend API'sini (FastAPI) çağırır. API adresi api.json'dan okunur
// (tünel URL'i değişince orası güncellenir); yoksa localhost'a düşer.
const DATA_URLS = ["../data/data.json", "./data.json", "data/data.json"];
let API = "http://localhost:8000"; // api.json ile ezilir

function tl(fiyat, pb) {
  if (fiyat == null || fiyat === "") return "—";
  const n = Number(String(fiyat).replace(/[^\d.,]/g, "").replace(",", "."));
  if (Number.isFinite(n)) {
    return new Intl.NumberFormat("tr-TR", {
      style: "currency",
      currency: (pb || "TRY").toUpperCase().slice(0, 3),
      maximumFractionDigits: 2,
    }).format(n);
  }
  return `${fiyat} ${pb || ""}`.trim();
}

function kart(u) {
  const el = document.createElement("a");
  el.className = "kart";
  el.href = u.link || "#";
  el.target = "_blank";
  el.rel = "noopener noreferrer";
  el.innerHTML = `
    <div class="gorsel" style="background-image:url('${u.gorsel || ""}')"></div>
    <div class="body">
      <span class="site">${u.site || ""}</span>
      <div class="ad">${u.ad || "İsimsiz ürün"}</div>
      <div class="fiyat">${tl(u.fiyat, u.para_birimi)}</div>
    </div>`;
  return el;
}

// Ortak render — hem başlangıç verisi hem canlı arama sonucu için.
function render(data) {
  const liste = document.getElementById("liste");
  const bos = document.getElementById("bos");
  liste.innerHTML = "";
  const urunler = (data && Array.isArray(data.urunler)) ? data.urunler : [];
  bos.hidden = urunler.length > 0;
  document.getElementById("sorgu").textContent = data && data.sorgu ? `“${data.sorgu}”` : "—";
  const a = (data && data.attributes) || {};
  document.getElementById("meta").textContent =
    [a.cinsiyet, a.renk, a.kategori, a.model, a.beden].filter(Boolean).join(" · ");
  document.getElementById("guncelleme").textContent =
    "Güncelleme: " + (data && data.guncelleme ? new Date(data.guncelleme).toLocaleString("tr-TR") : "—");
  urunler.forEach((u) => liste.appendChild(kart(u)));
}

async function loadApiBase() {
  try {
    const r = await fetch("api.json", { cache: "no-store" });
    if (r.ok) {
      const j = await r.json();
      if (j && j.api) API = j.api.replace(/\/+$/, "");
    }
  } catch (_) { /* localhost varsayılanı kalır */ }
}

async function yukleVarsayilan() {
  for (const url of DATA_URLS) {
    try {
      const r = await fetch(url, { cache: "no-store" });
      if (r.ok) { render(await r.json()); return; }
    } catch (_) { /* sıradaki */ }
  }
  render(null);
}

function durumGoster(html) {
  const d = document.getElementById("durum");
  d.hidden = !html;
  d.innerHTML = html || "";
}

async function ara(q) {
  const btn = document.getElementById("ara");
  btn.disabled = true;
  durumGoster('🔎 Arıyor… <span class="ipucu">(canlı — 3 site taranıyor, ~30-60 sn sürebilir)</span>');
  try {
    const r = await fetch(`${API}/search?q=${encodeURIComponent(q)}&limit=6`, { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const data = await r.json();
    render(data);
    durumGoster(data.urunler && data.urunler.length
      ? "" : "Sonuç bulunamadı — başka bir sorgu deneyin.");
  } catch (e) {
    durumGoster(
      "⚠️ Canlı arama şu an çalışmıyor (arama sunucusu kapalı olabilir). " +
      "Bu demo canlı aramayı ev makinesinde koşan bir pipeline ile yapar; " +
      "aşağıdaki hazır sonuçlar her zaman görüntülenir."
    );
  } finally {
    btn.disabled = false;
  }
}

document.getElementById("ara-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const q = document.getElementById("q").value.trim();
  if (q.length >= 2) ara(q);
});

(async function init() {
  await loadApiBase();
  await yukleVarsayilan();
})();
