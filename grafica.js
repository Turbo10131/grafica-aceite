// grafica.js
(() => {
  // === Config ===
  const HIST_URL = `${location.origin}/precio-aceite-historico.json?v=${Date.now()}`;

  // IDs esperados en tu HTML:
  // <select id="selTipo"> (Virgen Extra, Virgen, Lampante)
  // <select id="selAnio"> ("Todos los años" + años)
  // <button id="btnAnios">Años</button>
  // <button id="btnMeses">Meses</button>
  // <button id="btnDias">Días</button>
  // <div id="msg"></div>
  // <canvas id="chart"></canvas>

  const el = {
    tipo:  document.getElementById('selTipo')     || document.querySelector('#selTipo'),
    anio:  document.getElementById('selAnio')     || document.querySelector('#selAnio'),
    bA:    document.getElementById('btnAnios')    || document.querySelector('#btnAnios'),
    bM:    document.getElementById('btnMeses')    || document.querySelector('#btnMeses'),
    bD:    document.getElementById('btnDias')     || document.querySelector('#btnDias'),
    msg:   document.getElementById('msg')         || document.querySelector('#msg'),
    cnv:   document.getElementById('chart')       || document.querySelector('#chart'),
  };

  // Mapeo etiqueta selector -> clave JSON
  const CLAVE = {
    "Virgen Extra": "Aceite de oliva virgen extra",
    "Virgen":       "Aceite de oliva virgen",
    "Lampante":     "Aceite de oliva lampante"
  };

  let HIST = null;
  let modo = 'anios'; // anios | meses | dias
  let chart = null;

  function setMsg(texto) { if (el.msg) el.msg.textContent = texto || ''; }
  function log(...args){ console.log('[grafica]', ...args); }
  function err(...args){ console.error('[grafica]', ...args); }

  function parseISO(s){
    // s "YYYY-MM-DD"
    const [y,m,d] = s.split('-').map(n=>parseInt(n,10));
    return new Date(y,(m-1),d);
  }
  function fmt(n,dec=3){ return Number(n).toFixed(dec); }

  async function cargarHistorico(){
    setMsg('Cargando histórico…');
    try{
      const res = await fetch(HIST_URL, { cache:'no-store' });
      log('GET', HIST_URL, res.status);
      if(!res.ok){
        setMsg('No se pudo cargar el histórico (HTTP '+res.status+').');
        throw new Error('Bad status '+res.status);
      }
      const json = await res.json();
      // Validación mínima de shape
      const okKeys = [
        "Aceite de oliva virgen extra",
        "Aceite de oliva virgen",
        "Aceite de oliva lampante"
      ];
      for(const k of okKeys){
        if(!Array.isArray(json[k])){
          setMsg('JSON histórico no tiene el formato esperado.');
          throw new Error('Missing key '+k);
        }
      }
      HIST = json;
      setMsg('');
      log('HIST cargado', HIST);
    }catch(e){
      err('Error cargando histórico:', e);
      if(!el.msg.textContent) setMsg('No se pudo cargar el histórico.');
    }
  }

  function extraerAniosDisponibles(){
    // Obtiene el set de años presente en cualquier serie
    const years = new Set();
    if(!HIST) return [];
    Object.values(HIST).forEach(series => {
      series.forEach(p => {
        if(p && p.fecha){
          const y = parseInt(p.fecha.slice(0,4),10);
          if(y > 1900 && y < 2100) years.add(y);
        }
      });
    });
    return Array.from(years).sort((a,b)=>a-b);
  }

  function poblarSelectorAnios(){
    if(!el.anio) return;
    const anos = extraerAniosDisponibles();
    el.anio.innerHTML = '';
    const optAll = document.createElement('option');
    optAll.value = 'all';
    optAll.textContent = 'Todos los años';
    el.anio.appendChild(optAll);
    anos.forEach(y=>{
      const o = document.createElement('option');
      o.value = String(y);
      o.textContent = y;
      el.anio.appendChild(o);
    });
    el.anio.value = 'all';
  }

  function datosFiltrados(tipoLabel){
    if(!HIST) return [];
    const clave = CLAVE[tipoLabel];
    if(!clave) return [];
    const serie = HIST[clave] || [];
    const sel = (el.anio && el.anio.value) || 'all';
    if(sel === 'all') return serie.slice();
    const y = parseInt(sel,10);
    return serie.filter(p => parseInt(p.fecha.slice(0,4),10) === y);
  }

  function agruparPorAnio(puntos){
    const map = new Map(); // year -> {sum, n}
    for(const p of puntos){
      const y = parseInt(p.fecha.slice(0,4),10);
      const obj = map.get(y) || {sum:0,n:0};
      obj.sum += Number(p.precio_eur_kg);
      obj.n++;
      map.set(y,obj);
    }
    const labels = Array.from(map.keys()).sort((a,b)=>a-b);
    const data = labels.map(y => map.get(y).sum / map.get(y).n);
    return { labels, data };
  }

  function agruparPorMes(puntos){
    // Devuelve promedio por cada mes del año seleccionado
    const map = new Map(); // 'YYYY-MM' -> {sum,n}
    for(const p of puntos){
      const k = p.fecha.slice(0,7);
      const obj = map.get(k) || {sum:0,n:0};
      obj.sum += Number(p.precio_eur_kg);
      obj.n++;
      map.set(k,obj);
    }
    const labels = Array.from(map.keys()).sort();
    const data = labels.map(k => map.get(k).sum / map.get(k).n);
    return { labels, data };
  }

  function porDia(puntos){
    // Ordena por fecha y coloca cada punto
    const ordenados = puntos.slice().sort((a,b)=> a.fecha.localeCompare(b.fecha));
    const labels = ordenados.map(p=>p.fecha);
    const data = ordenados.map(p=>Number(p.precio_eur_kg));
    return { labels, data };
  }

  function render(){
    if(!el.cnv) return;
    const tipoLabel = el.tipo ? el.tipo.value : 'Virgen Extra';
    const serie = datosFiltrados(tipoLabel);

    if(!serie.length){
      setMsg('No hay datos históricos para mostrar.');
      if(chart){ chart.destroy(); chart = null; }
      return;
    } else {
      setMsg('');
    }

    let labels = [], data = [];
    if(modo === 'anios'){
      const g = agruparPorAnio(serie);
      labels = g.labels; data = g.data;
    }else if(modo === 'meses'){
      const g = agruparPorMes(serie);
      labels = g.labels; data = g.data;
    }else{
      const g = porDia(serie);
      labels = g.labels; data = g.data;
    }

    if(chart) chart.destroy();
    chart = new Chart(el.cnv, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: `Aceite de oliva ${tipoLabel.toLowerCase()}`,
          data,
          fill: true,
          tension: 0.2,
          borderColor: '#1f6feb',
          backgroundColor: 'rgba(31,111,235,.12)',
          pointRadius: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true },
          tooltip: { mode: 'index', intersect: false }
        },
        scales: {
          x: { title: { display: true, text: modo === 'anios' ? 'Año' : (modo==='meses'?'Mes':'Día') } },
          y: { title: { display: true, text: '€/kg' }, beginAtZero: false }
        }
      }
    });
  }

  function bind(){
    el.tipo && el.tipo.addEventListener('change', render);
    el.anio && el.anio.addEventListener('change', render);
    el.bA && el.bA.addEventListener('click', () => { modo = 'anios'; render(); activar(el.bA); });
    el.bM && el.bM.addEventListener('click', () => { modo = 'meses'; render(); activar(el.bM); });
    el.bD && el.bD.addEventListener('click', () => { modo = 'dias';  render(); activar(el.bD); });
  }

  function activar(btn){
    [el.bA,el.bM,el.bD].forEach(b=> b && b.classList.remove('active'));
    btn && btn.classList.add('active');
  }

  async function init(){
    try{
      await cargarHistorico();
      if(!HIST) return; // ya se mostró el mensaje

      // Rellenar el selector de años
      poblarSelectorAnios();

      // Si tu <select id="selTipo"> tiene values iguales a las etiquetas, lo dejamos.
      // Si necesitas defaults, ponlos aquí:
      if(el.tipo && !el.tipo.value){ el.tipo.value = 'Virgen Extra'; }

      bind();
      activar(el.bA);
      render();
    }catch(e){
      err(e);
      setMsg('No se pudo inicializar la gráfica.');
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
