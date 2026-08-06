// K5 — Sunum: data.json'u çek, ürünleri site/link/fiyat olarak listele.
// GitHub Pages'te /site kökten yayınlanırsa data.json bir üst dizinde olur.
const DATA_URLS = ["../data/data.json", "./data.json", "data/data.json"];

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

async function yukle() {
  let data = null;
  for (const url of DATA_URLS) {
    try {
      const r = await fetch(url, { cache: "no-store" });
      if (r.ok) { data = await r.json(); break; }
    } catch (_) { /* sıradaki yolu dene */ }
  }
  const liste = document.getElementById("liste");
  const bos = document.getElementById("bos");
  if (!data || !Array.isArray(data.urunler) || data.urunler.length === 0) {
    bos.hidden = false;
    return;
  }
  document.getElementById("sorgu").textContent = `“${data.sorgu || ""}”`;
  const a = data.attributes || {};
  document.getElementById("meta").textContent = [a.cinsiyet, a.renk, a.kategori, a.model, a.beden]
    .filter(Boolean).join(" · ");
  document.getElementById("guncelleme").textContent =
    "Güncelleme: " + (data.guncelleme ? new Date(data.guncelleme).toLocaleString("tr-TR") : "—");
  data.urunler.forEach((u) => liste.appendChild(kart(u)));
}

yukle();
