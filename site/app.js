// K5 — Sunum: canlı arama (backend API) + landing/loading/sonuç görünümleri.
// API adresi api.json'dan okunur (tünel URL'i); yoksa localhost'a düşer.
let API = "http://localhost:8000";

const $ = (id) => document.getElementById(id);
const PROGRESS_MS = 30_000;
let progressRaf = null;

function progressBaslat() {
  const bar = $("progress-bar");
  const track = bar.parentElement;
  bar.style.transition = "none";
  bar.style.width = "0%";
  track.setAttribute("aria-valuenow", "0");
  cancelAnimationFrame(progressRaf);
  progressRaf = requestAnimationFrame(() => {
    bar.style.transition = `width ${PROGRESS_MS}ms linear`;
    bar.style.width = "100%";
  });
}

function progressBitir() {
  cancelAnimationFrame(progressRaf);
  const bar = $("progress-bar");
  const track = bar.parentElement;
  bar.style.transition = "width 0.25s ease";
  bar.style.width = "100%";
  track.setAttribute("aria-valuenow", "100");
}

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
  const g = u.gorsel || "";
  // <img> + onerror: yüklenmeyen görselde boş/bozuk alan yerine temiz placeholder.
  const img = g
    ? `<img src="${g}" alt="" loading="lazy" referrerpolicy="no-referrer"
           onerror="this.closest('.gorsel').classList.add('bos');this.remove();">`
    : "";
  el.innerHTML = `
    <div class="gorsel${g ? "" : " bos"}">${img}</div>
    <div class="body">
      <span class="site">${u.site || ""}</span>
      <div class="ad">${u.ad || "İsimsiz ürün"}</div>
      <div class="fiyat">${tl(u.fiyat, u.para_birimi)}</div>
    </div>`;
  return el;
}

// --- Görünüm durumları: tek seferde biri görünür ---
function view(name) {
  $("welcome").hidden = name !== "welcome";
  $("loading").hidden = name !== "loading";
  $("sonuc").hidden = name !== "sonuc";
}

function durumGoster(html) {
  $("durum").hidden = !html;
  $("durum").innerHTML = html || "";
}

function anasayfa() {
  durumGoster("");
  $("q").value = "";
  $("liste").innerHTML = "";
  view("welcome");
  $("q").focus();
}

function sonucGoster(data) {
  const liste = $("liste");
  liste.innerHTML = "";
  const urunler = (data && Array.isArray(data.urunler)) ? data.urunler : [];
  $("sorgu").textContent = data && data.sorgu ? `“${data.sorgu}”` : "—";
  $("guncelleme").textContent =
    "Güncelleme: " + (data && data.guncelleme ? new Date(data.guncelleme).toLocaleString("tr-TR") : "—");
  urunler.forEach((u) => liste.appendChild(kart(u)));
  $("bos").hidden = urunler.length > 0;
  view("sonuc");
}

async function loadApiBase() {
  try {
    const r = await fetch("api.json", { cache: "no-store" });
    if (r.ok) {
      const j = await r.json();
      if (j && j.api) API = j.api.replace(/\/+$/, "");
    }
  } catch (_) { /* localhost varsayılanı */ }
}

async function ara(q) {
  durumGoster("");
  $("ara").disabled = true;
  $("loading-q").textContent = q;
  view("loading");
  progressBaslat();
  try {
    const r = await fetch(`${API}/search?q=${encodeURIComponent(q)}&limit=6`, { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const data = await r.json();
    sonucGoster(data);
    if (!data.urunler || data.urunler.length === 0) {
      durumGoster("Sonuç bulunamadı — başka bir sorgu dene.");
    }
  } catch (e) {
    view("welcome");
    durumGoster(
      "⚠️ Canlı arama şu an çalışmıyor (arama sunucusu kapalı olabilir). " +
      "Bu demo, aramayı ev makinesinde koşan bir pipeline ile yapar."
    );
  } finally {
    progressBitir();
    $("ara").disabled = false;
  }
}

function baslat(q) {
  q = (q || "").trim();
  if (q.length < 2) return;
  $("q").value = q;
  ara(q);
}

// --- Olaylar ---
$("ara-form").addEventListener("submit", (e) => { e.preventDefault(); baslat($("q").value); });
$("geri").addEventListener("click", anasayfa);
$("logo").addEventListener("click", (e) => { e.preventDefault(); anasayfa(); });
$("ornekler").addEventListener("click", (e) => {
  if (e.target.classList.contains("ornek")) baslat(e.target.textContent);
});

(async function init() {
  await loadApiBase();
  view("welcome");
})();
