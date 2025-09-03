// ---- Configuración y estado ----
const TIPO_LABEL = {
  virgen_extra: "Aceite de oliva virgen extra",
  virgen:       "Aceite de oliva virgen",
  lampante:     "Aceite de oliva lampante",
};

const HIST_URL = `precio-aceite-historico.json?v=${Date.now()}`;

let HISTORICO = {};   // JSON histórico completo
let mode = "years";   // years | months | days
let chart = null;

// ---- Utilidades ----
const $ = (id) => document.getElementById(id);

function parseISO(s) {
  // s = "YYYY-MM-DD"
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function avg(nums) {
  if (!nums.length) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

// Devuelve array [{fecha:Date, precio:number}] de un tipo
function datosTipo(tipo) {
  const arr = HISTORICO[TIPO_LABEL[tipo]] || [];
  return arr
    .map((d) => ({ fecha: parseISO(d.fecha), precio: Number(d.precio_eur_kg) }))
    .filter((d) => d.precio > 0 && d.precio < 20)
    .sort((a, b) => a.fecha - b.fecha);
}

function uniqueYearsFor(tipo) {
  const set = new Set(datosTipo(tipo).map((d) => d.fecha.getFullYear()));
  return Array.from(set).sort((a, b) => a - b);
}

function setActive(btn) {
  document.querySelectorAll(".btn[data-mode]").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
}

// ---- Preparación de datos según modo ----
function dataYears(tipo) {
  const rows = datosTipo(tipo);
  const buckets = new Map(); // year -> [precios]
  rows.forEach(({ fecha, precio }) => {
    const y = fecha.getFullYear();
    if (!buckets.has(y)) buckets.set(y, []);
    buckets.get(y).push(precio);
  });

  const years = Array.from(buckets.keys()).sort((a, b) => a - b);
  const values = years.map((y) => Number(avg(buckets.get(y)).toFixed(3)));

  return {
    labels: years.map(String),
    data: values,
    xTitle: "Año",
  };
}

function dataMonths(tipo, yearOpt) {
  const rows = datosTipo(tipo);
  let filtered = rows;

  if (yearOpt && yearOpt !== "all") {
    const y = Number(yearOpt);
    filtered = rows.filter((r) => r.fecha.getFullYear() === y);
  } else {
    // último año natural de datos si no se escoge año
    const maxDate = rows.at(-1)?.fecha;
    if (!maxDate) return { labels: [], data: [], xTitle: "Mes" };
    const from = new Date(maxDate);
    from.setFullYear(from.getFullYear() - 1);
    filtered = rows.filter((r) => r.fecha >= from);
  }

  const buckets = new Map(); // "YYYY-MM" -> [precios]
  filtered.forEach(({ fecha, precio }) => {
    const key = `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, "0")}`;
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(precio);
  });

  const keys = Array.from(buckets.keys()).sort();
  const values = keys.map((k) => Number(avg(buckets.get(k)).toFixed(3)));

  return {
    labels: keys, // YYYY-MM
    data: values,
    xTitle: "Mes",
  };
}

function dataDays(tipo, yearOpt) {
  const rows = datosTipo(tipo);
  let filtered = rows;

  if (yearOpt && yearOpt !== "all") {
    const y = Number(yearOpt);
    filtered = rows.filter((r) => r.fecha.getFullYear() === y);
  } else {
    // últimos ~365 días si no se escoge año
    const maxDate = rows.at(-1)?.fecha;
    if (!maxDate) return { labels: [], data: [], xTitle: "Día" };
    const from = new Date(maxDate);
    from.setFullYear(from.getFullYear() - 1);
    filtered = rows.filter((r) => r.fecha >= from);
  }

  return {
    labels: filtered.map((r) => r.fecha.toISOString().slice(0, 10)),
    data: filtered.map((r) => r.precio),
    xTitle: "Día",
  };
}

// ---- Render de gráfica ----
function render() {
  const tipo = $("tipo").value;
  const yearSel = $("anio").value;

  const msg = $("grafico-msg");
  msg.textContent = "";

  let payload;
  if (mode === "years") payload = dataYears(tipo);
  else if (mode === "months") payload = dataMonths(tipo, yearSel);
  else payload = dataDays(tipo, yearSel);

  const { labels, data, xTitle } = payload;

  if (!labels.length) {
    if (chart) { chart.destroy(); chart = null; }
    msg.textContent = "No hay datos históricos para mostrar.";
    return;
  }

  if (chart) chart.destroy();

  const ctx = $("grafico").getContext("2d");
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: TIPO_LABEL[tipo],
        data,
        tension: 0.2,
        borderColor: "#1f6feb",
        backgroundColor: "rgba(31,111,235,.12)",
        fill: true,
        pointRadius: 3
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: true },
        tooltip: { mode: "index", intersect: false }
      },
      scales: {
        x: { title: { display: true, text: xTitle } },
        y: { title: { display: true, text: "€/kg" } }
      }
    }
  });
}

// ---- UI ----
function populateYears() {
  const tipo = $("tipo").value;
  const years = uniqueYearsFor(tipo);
  const sel = $("anio");
  sel.innerHTML = `<option value="all">Todos los años</option>` +
    years.map((y) => `<option value="${y}">${y}</option>`).join("");
}

async function init() {
  try {
    const res = await fetch(HIST_URL, { cache: "no-store" });
    HISTORICO = await res.json();
  } catch (e) {
    $("grafico-msg").textContent = "No se pudo cargar el histórico.";
    return;
  }

  populateYears();
  render();

  $("tipo").addEventListener("change", () => { populateYears(); render(); });
  $("anio").addEventListener("change", render);

  document.querySelectorAll(".btn[data-mode]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      setActive(btn);
      mode = btn.dataset.mode;
      render();
    });
  });
}

document.addEventListener("DOMContentLoaded", init);
