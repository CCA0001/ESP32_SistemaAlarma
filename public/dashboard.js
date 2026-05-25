'use strict';

/* ─── Configuración Firebase ────────────────── */
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getFirestore, collection, query, orderBy, limit, onSnapshot } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyC-VMERxR38vxhEusqAA8yv6tZvv4QJoeU",
  authDomain: "dashboard-esp32-d4b3b.firebaseapp.com",
  projectId: "dashboard-esp32-d4b3b",
  storageBucket: "dashboard-esp32-d4b3b.firebasestorage.app",
  messagingSenderId: "367583210826",
  appId: "1:367583210826:web:11da61ad8e8ea149c6e5b3"
};

const app = initializeApp(firebaseConfig);
const db  = getFirestore(app);

/* ─── Configuración ─────────────────────────── */
const LUX_MAX      = 100;
const MAX_RECORDS  = 100;

/* ─── Estado global ─────────────────────────── */
const state = {
  sessionMax   : null,
  sessionMaxTs : null,
  sessionMin   : null,
  sessionMinTs : null,
};

/* ─── Referencias DOM ───────────────────────── */
const dom = {
  lastUpdate   : document.getElementById('last-update'),
  kpiCurrent   : document.getElementById('kpi-current'),
  kpiBar       : document.getElementById('kpi-bar'),
  kpiMax       : document.getElementById('kpi-max'),
  kpiMaxTime   : document.getElementById('kpi-max-time'),
  kpiMin       : document.getElementById('kpi-min'),
  kpiMinTime   : document.getElementById('kpi-min-time'),
  kpiAvg       : document.getElementById('kpi-avg'),
  gaugeArc     : document.getElementById('gauge-arc'),
  gaugePct     : document.getElementById('gauge-pct'),
  readingsBody : document.getElementById('readings-body'),
  tableCount   : document.getElementById('table-count'),
  placeholder  : document.getElementById('chart-placeholder'),
  statusDot    : document.querySelector('.status-dot'),
  statusLabel  : document.querySelector('.status-label'),
};

/* ─── Chart.js ──────────────────────────────── */
const ctx   = document.getElementById('lux-chart').getContext('2d');
const chart = new Chart(ctx, {
  type : 'line',
  data : {
    labels   : [],
    datasets : [{
      label                : 'Luminosidad (lux)',
      data                 : [],
      borderColor          : '#FF5252',
      backgroundColor      : 'rgba(211, 47, 47, 0.12)',
      borderWidth          : 2,
      pointRadius          : 3,
      pointBackgroundColor : '#FF5252',
      pointBorderColor     : '#1A1A1A',
      pointBorderWidth     : 1.5,
      tension              : 0.35,
      fill                 : true,
    }],
  },
  options : {
    responsive          : true,
    maintainAspectRatio : false,
    animation           : { duration: 300 },
    plugins : { legend : { display: false } },
    scales : {
      x : {
        ticks : { color: '#363636', font: { family: 'DM Mono', size: 10 }, maxRotation: 0 },
        grid  : { color: 'rgba(255,255,255,0.04)' },
      },
      y : {
        min   : 0,
        max   : LUX_MAX,
        ticks : { color: '#363636', font: { family: 'DM Mono', size: 10 }, stepSize: 250 },
        grid  : { color: 'rgba(255,255,255,0.04)' },
      },
    },
  },
});

/* ─── Helpers ───────────────────────────────── */
function fmtTime(ts) {
  if (!ts) return '--:--:--';
  const d = ts.toDate ? ts.toDate() : new Date(ts);
  return d.toTimeString().slice(0, 8);
}

function luxBadge(value) {
  if (value >= 700) return '<span class="badge badge--alto">Alto</span>';
  if (value >= 300) return '<span class="badge badge--medio">Medio</span>';
  return '<span class="badge badge--bajo">Bajo</span>';
}

function setStatus(online) {
  dom.statusDot.classList.toggle('status-dot--online',  online);
  dom.statusDot.classList.toggle('status-dot--offline', !online);
  dom.statusLabel.textContent = online ? 'Sensor activo' : 'Sin conexión';
}

/* ─── Renderizar datos ──────────────────────── */
function render(rows) {
  if (!rows.length) return;

  chart.data.labels           = rows.map(r => fmtTime(r.creado_en));
  chart.data.datasets[0].data = rows.map(r => parseFloat(r.valor));
  chart.update('none');
  dom.placeholder.classList.add('hidden');

  const last  = rows[rows.length - 1];
  const value = parseFloat(last.valor);

  dom.kpiCurrent.textContent = value;
  dom.kpiBar.style.width     = Math.min((value / LUX_MAX) * 100, 100) + '%';
  dom.lastUpdate.textContent = fmtTime(last.creado_en);

  rows.forEach(r => {
    const v = parseFloat(r.valor);
    if (state.sessionMax === null || v > state.sessionMax) {
      state.sessionMax   = v;
      state.sessionMaxTs = r.creado_en;
    }
    if (state.sessionMin === null || v < state.sessionMin) {
      state.sessionMin   = v;
      state.sessionMinTs = r.creado_en;
    }
  });

  dom.kpiMax.textContent     = state.sessionMax;
  dom.kpiMaxTime.textContent = fmtTime(state.sessionMaxTs);
  dom.kpiMin.textContent     = state.sessionMin;
  dom.kpiMinTime.textContent = fmtTime(state.sessionMinTs);

  const avg = Math.round(rows.reduce((s, r) => s + parseFloat(r.valor), 0) / rows.length);
  dom.kpiAvg.textContent = avg;

  const ARC_LEN = 251;
  const filled  = Math.min(value / LUX_MAX, 1) * ARC_LEN;
  dom.gaugeArc.setAttribute('stroke-dasharray', `${filled.toFixed(1)} ${ARC_LEN}`);
  dom.gaugePct.textContent = Math.round((value / LUX_MAX) * 100) + '%';

  dom.readingsBody.innerHTML = '';
  [...rows].reverse().slice(0, MAX_RECORDS).forEach((r, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="color:rgba(255,255,255,0.3)">${i + 1}</td>
      <td>${fmtTime(r.creado_en)}</td>
      <td>${parseFloat(r.valor)}</td>
      <td>${luxBadge(parseFloat(r.valor))}</td>
    `;
    dom.readingsBody.appendChild(tr);
  });
  dom.tableCount.textContent = Math.min(rows.length, MAX_RECORDS) + ' registros';
}

/* ─── Escuchar Firestore en tiempo real ─────── */
const q = query(
  collection(db, "lecturas"),
  limit(60)
);

onSnapshot(q,
  snapshot => {
    const rows = snapshot.docs.map(doc => doc.data());
    setStatus(true);
    render(rows);
  },
  err => {
    console.error('[LuxPanel] Error Firestore:', err);
    setStatus(false);
  }
);