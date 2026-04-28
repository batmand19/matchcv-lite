// ---- Config ----
const BACKEND_URL = (() => {
  if (typeof BACKEND_OVERRIDE !== 'undefined') return BACKEND_OVERRIDE;
  const h = window.location.hostname;
  if (h === 'localhost' || h === '127.0.0.1' || h === '') return 'http://localhost:8000';
  return 'https://matchcv-backend.onrender.com';
})();

// ---- Oferta de ejemplo ----
const OFERTA_EJEMPLO = `Analista de Datos y Planeación Financiera

Misión del cargo
Transformar datos financieros y operacionales en insights accionables que soporten la toma de decisiones estratégicas del área de Planeación Financiera. El analista será responsable de construir, mantener y automatizar reportes clave, y de desarrollar modelos predictivos que respalden el proceso de forecast y presupuesto anual de la compañía.

Funciones principales
- Analizar y procesar grandes volúmenes de datos financieros y operacionales provenientes de múltiples sistemas internos.
- Construir y mantener dashboards interactivos en Power BI para el seguimiento de KPIs de rentabilidad, ejecución presupuestal y variaciones de margen, utilizados por tres gerencias de forma semanal.
- Elaborar modelos de planeación financiera y forecast en Excel para las diferentes unidades de negocio de la organización.
- Automatizar los procesos de extracción, transformación y carga (ETL) de datos desde distintos sistemas usando SQL y Python.
- Gestionar y validar la integridad de los datos en las bases de datos del área financiera.
- Generar reportes ejecutivos con análisis de variaciones presupuestales y recomendaciones accionables para la alta dirección.
- Colaborar con el equipo de finanzas para identificar oportunidades de optimización y eficiencia en los procesos de análisis de datos.
- Documentar procesos, metodologías y modelos para garantizar la continuidad del conocimiento en el área.

Experiencia requerida
- Mínimo 2 años de experiencia en análisis de datos, planeación financiera o inteligencia de negocios.
- Experiencia comprobable en construcción de dashboards e indicadores en Power BI.
- Manejo avanzado de Excel, incluyendo tablas dinámicas, Power Query y fórmulas complejas.
- Experiencia en escritura de consultas SQL sobre bases de datos relacionales (PostgreSQL, MySQL o SQL Server).
- Deseable experiencia con Python para análisis de datos (pandas, numpy, matplotlib).
- Deseable experiencia con herramientas de gestión de versiones como Git.

Formación académica
- Profesional en Ingeniería Industrial, Administración de Empresas, Economía, Contaduría Pública o carreras afines con énfasis cuantitativo.
- Deseable certificación en Power BI (Microsoft PL-300) o cursos especializados en análisis de datos.

Habilidades y competencias
- Pensamiento analítico y alta orientación al detalle en el manejo de datos numéricos.
- Capacidad para comunicar hallazgos de datos de forma clara a audiencias no técnicas.
- Inglés básico-intermedio para lectura de documentación técnica.

Herramientas requeridas
Excel avanzado, Power BI, SQL, Python, pandas, numpy, Git, análisis de datos, planeación financiera, KPIs, dashboard, automatización.`;

// ---- State ----
let tabActiva       = 'archivo';
let ultimoResultado = null;

// ---- Tab switching ----
function switchTab(tab) {
  tabActiva = tab;
  document.getElementById('tabArchivo').classList.toggle('active', tab === 'archivo');
  document.getElementById('tabTexto').classList.toggle('active',   tab === 'texto');
  document.getElementById('panelArchivo').style.display = tab === 'archivo' ? '' : 'none';
  document.getElementById('panelTexto').style.display   = tab === 'texto'   ? '' : 'none';
}

// ---- File drag & drop ----
const fileDrop  = document.getElementById('fileDrop');
const cvFile    = document.getElementById('cvFile');
const fileLabel = document.getElementById('fileLabel');

cvFile.addEventListener('change', updateFileLabel);
fileDrop.addEventListener('dragover',  e => { e.preventDefault(); fileDrop.classList.add('dragover'); });
fileDrop.addEventListener('dragleave', ()  => fileDrop.classList.remove('dragover'));
fileDrop.addEventListener('drop', e => {
  e.preventDefault();
  fileDrop.classList.remove('dragover');
  if (e.dataTransfer.files.length) {
    const dt = new DataTransfer();
    dt.items.add(e.dataTransfer.files[0]);
    cvFile.files = dt.files;
    updateFileLabel();
  }
});

function updateFileLabel() {
  const file = cvFile.files[0];
  if (!file) return;
  fileLabel.innerHTML = `
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" class="mx-auto mb-2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14,2 14,8 20,8"/>
    </svg>
    <p style="font-size:0.95rem;font-weight:500;color:var(--accent);">${escapeHtml(file.name)}</p>
    <p style="font-size:0.75rem;color:var(--muted);margin-top:5px;">${(file.size/1024).toFixed(0)} KB · Listo</p>
  `;
}

// Character counter
document.getElementById('cvTexto').addEventListener('input', function () {
  const len     = this.value.length;
  const counter = document.getElementById('cvTextoCount');
  counter.textContent = len + ' caracteres' + (len < 100 ? ' (mínimo 100)' : ' ✓');
  counter.style.color = len >= 100 ? 'var(--accent)' : 'var(--muted)';
});

// ---- Front-end validation ----
function validarFormulario() {
  const oferta = (document.getElementById('ofertaTexto').value || '').trim();
  if (oferta.length < 100) {
    showError('La oferta laboral debe tener al menos 100 caracteres. Pega el texto completo de la vacante.');
    return false;
  }
  if (tabActiva === 'archivo') {
    const file = cvFile.files[0];
    if (!file) { showError('Por favor selecciona tu archivo CV (PDF, DOCX o TXT).'); return false; }
    if (file.size > 5 * 1024 * 1024) {
      showError(`El archivo "${escapeHtml(file.name)}" supera el límite de 5 MB.`);
      return false;
    }
    const ext = file.name.toLowerCase().split('.').pop();
    if (!['pdf','docx','txt'].includes(ext)) {
      showError(`Formato ".${ext}" no soportado. Sube un archivo PDF, DOCX o TXT.`);
      return false;
    }
  } else {
    const cvText = (document.getElementById('cvTexto').value || '').trim();
    if (cvText.length < 100) {
      showError('El texto del CV debe tener al menos 100 caracteres.');
      return false;
    }
  }
  return true;
}

// ---- Load CV example (does NOT touch oferta) ----
async function cargarCVEjemplo() {
  const btn = document.getElementById('btnCVEjemplo');
  btn.disabled = true;
  btn.textContent = 'Cargando...';
  try {
    const resp   = await fetch('cv_ejemplo.txt');
    const cvText = resp.ok ? await resp.text() : null;
    const text   = (cvText && cvText.trim().length >= 100) ? cvText.trim() : getFallbackCV();
    if (tabActiva === 'archivo') {
      const blob = new Blob([text], { type: 'text/plain' });
      const file = new File([blob], 'cv_ejemplo.txt', { type: 'text/plain' });
      const dt   = new DataTransfer();
      dt.items.add(file);
      cvFile.files = dt.files;
      updateFileLabel();
    } else {
      document.getElementById('cvTexto').value = text;
      document.getElementById('cvTexto').dispatchEvent(new Event('input'));
    }
  } catch {
    switchTab('texto');
    document.getElementById('cvTexto').value = getFallbackCV();
    document.getElementById('cvTexto').dispatchEvent(new Event('input'));
  } finally {
    btn.disabled    = false;
    btn.textContent = '📄 Cargar CV de ejemplo';
  }
}

// ---- Load offer example (does NOT touch CV) ----
function cargarOfertaEjemplo() {
  document.getElementById('ofertaTexto').value = OFERTA_EJEMPLO;
  const ta = document.getElementById('ofertaTexto');
  ta.style.borderColor = 'var(--accent)';
  setTimeout(() => { ta.style.borderColor = ''; }, 1200);
}

function getFallbackCV() {
  return `Laura Marcela Rincón Ospina — Analista de Datos y Planeación Financiera
Bogotá, Colombia | laura.rincon@email.com

PERFIL PROFESIONAL
Analista de Datos con 4 años de experiencia en planeación financiera, análisis de datos y automatización de reportes. Manejo avanzado de Excel, Power BI y SQL. Orientada a resultados con logros comprobables en reducción de tiempos y optimización de procesos.

EXPERIENCIA

Analista de Planeación Financiera Senior — Grupo Empresarial Andino (Enero 2022 - Presente)
- Automaticé el cierre financiero mensual con Excel y Power BI, reduciendo tiempo de reportes en un 40%.
- Desarrollé dashboards en Power BI para seguimiento de KPIs de rentabilidad (consultados por 3 gerencias).
- Analicé base de 50.000 clientes con SQL, logrando un incremento del 18% en ingresos del segmento estratégico.
- Construí modelo de forecast financiero en Excel con 92% de precisión para 5 unidades de negocio.
- Automaticé extracción de datos SAP con VBA, eliminando 12 horas de trabajo manual mensual.

Analista de Datos Junior — Finanzas Digitales Colombia (Marzo 2020 - Diciembre 2021)
- Construí reportes de cartera con SQL en PostgreSQL sobre más de 2 millones de registros.
- Diseñé tableros en Power BI que mejoraron visibilidad de indicadores en un 35%.
- Automaticé informes regulatorios en Excel, reduciendo errores en un 60%.

HABILIDADES
Excel avanzado (Power Query, tablas dinámicas, VBA), Power BI, SQL, Python (pandas, numpy), análisis de datos, planeación financiera, KPIs, dashboard, Git.

EDUCACIÓN
Ingeniería Industrial — Universidad de los Andes (2019)
Certificación Power BI PL-300 — Microsoft (2022)`;
}

// ---- Form submit ----
const form         = document.getElementById('matchForm');
const submitBtn    = document.getElementById('submitBtn');
const resultadoDiv = document.getElementById('resultado');
const desgloseDiv  = document.getElementById('desgloseCategories');
const kwDiv        = document.getElementById('palabrasClave');
const atsDiv       = document.getElementById('contextoAts');
const encuestaDiv  = document.getElementById('encuesta');
const copyWrapper  = document.getElementById('copyBtnWrapper');

form.addEventListener('submit', async e => {
  e.preventDefault();
  if (!validarFormulario()) return;

  const oferta = document.getElementById('ofertaTexto').value.trim();
  const formData = new FormData();
  formData.append('oferta_texto', oferta);
  if (tabActiva === 'archivo') {
    formData.append('file', cvFile.files[0]);
  } else {
    formData.append('cv_texto', document.getElementById('cvTexto').value.trim());
  }

  submitBtn.disabled     = true;
  submitBtn.innerHTML    = `<span class="spinner"></span> Analizando...`;
  resultadoDiv.className = 'hidden';
  resultadoDiv.innerHTML = '';
  desgloseDiv.className  = 'hidden';
  desgloseDiv.innerHTML  = '';
  kwDiv.className        = 'hidden';
  kwDiv.innerHTML        = '';
  atsDiv.className       = 'hidden';
  atsDiv.innerHTML       = '';
  copyWrapper.classList.add('hidden');

  try {
    let res;
    try {
      res = await fetch(`${BACKEND_URL}/analizar`, { method: 'POST', body: formData });
    } catch (netErr) {
      showError(`Error de conexión con el servidor. Asegúrate de que el backend esté corriendo en ${BACKEND_URL}. Detalle: ${netErr.message}`);
      return;
    }

    let data;
    try {
      data = await res.json();
    } catch {
      showError(`El servidor respondió con un formato inesperado (HTTP ${res.status}).`);
      return;
    }

    if (data.exito) {
      ultimoResultado = data;
      renderResultado(data);
      renderDesglose(data.desglose || {});
      renderPalabrasClave(data.palabras_clave_oferta || []);
      renderContextoAts(data.contexto_ats || []);
      copyWrapper.classList.remove('hidden');
      encuestaDiv.classList.remove('hidden');
      setTimeout(() => encuestaDiv.scrollIntoView({ behavior: 'smooth', block: 'start' }), 800);
    } else {
      showError(`Error del servidor: ${data.error || 'Error desconocido.'}`);
    }
  } finally {
    submitBtn.disabled  = false;
    submitBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      Analizar encaje`;
  }
});

// ---- Render resultado ----
function renderResultado(data) {
  const { encaje_global, nivel, aporta, brechas, recomendaciones, frase_final } = data;

  const badgeClass = nivel === 'Buen encaje' ? 'badge-good' : nivel === 'Encaje medio' ? 'badge-mid' : 'badge-low';
  const barColor   = nivel === 'Buen encaje' ? 'var(--accent)' : nivel === 'Encaje medio' ? 'var(--warn)' : 'var(--danger)';
  const fraseBg    = nivel === 'Buen encaje' ? '#f0faf4' : nivel === 'Encaje medio' ? 'var(--warn-light)' : 'var(--danger-light)';

  function buildList(items, emptyMsg) {
    if (!items || !items.length) return `<p style="font-size:0.9rem;color:var(--muted);">${emptyMsg}</p>`;
    return items.map(item => `
      <div class="result-list-item">
        <span class="emoji">${item.emoji}</span>
        <span>${escapeHtml(item.text)}</span>
      </div>`).join('');
  }

  resultadoDiv.innerHTML = `
    <div class="card p-6 md:p-8 fade-in">
      <p class="syne font-bold mb-6" style="font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);">Resultado del análisis</p>

      <div class="flex items-end gap-5 mb-5">
        <span class="numero-encaje" id="animatedScore">0%</span>
        <div style="padding-bottom:6px;">
          <span class="badge ${badgeClass}">${escapeHtml(nivel)}</span>
          <p style="font-size:0.78rem;color:var(--muted);margin-top:6px;line-height:1.4;">Encaje global con la vacante</p>
        </div>
      </div>

      <div class="progress-bg mb-10">
        <div class="progress-fill" id="progressFill" style="background:${barColor};"></div>
      </div>

      <div class="space-y-5">
        <div class="section-aportes fade-in stagger-1">
          <p class="section-title" style="color:var(--accent);">Lo que aportas</p>
          ${buildList((aporta||[]).map(a=>({emoji:'✅',text:a})), 'No se detectaron fortalezas destacadas.')}
        </div>
        <div class="section-brechas fade-in stagger-2">
          <p class="section-title" style="color:var(--danger);">Brechas detectadas</p>
          ${buildList((brechas||[]).map(b=>({emoji:'⚠️',text:b})), 'No se detectaron brechas significativas.')}
        </div>
        <div class="section-recos fade-in stagger-3">
          <p class="section-title" style="color:#1d4ed8;">Recomendaciones</p>
          ${buildList((recomendaciones||[]).map(r=>({emoji:'📝',text:r})), 'No hay recomendaciones adicionales.')}
        </div>
      </div>

      <hr class="divider">
      <div class="rounded-xl p-5 text-center" style="background:${fraseBg};">
        <p class="syne font-bold" style="font-size:1rem;line-height:1.5;">${escapeHtml(frase_final)}</p>
      </div>
    </div>
  `;

  resultadoDiv.classList.remove('hidden');
  resultadoDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
  setTimeout(() => {
    animateNumber('animatedScore', encaje_global, 1200);
    document.getElementById('progressFill').style.width = `${encaje_global}%`;
  }, 80);
}

// ---- Render desglose category bars ----
function renderDesglose(desglose) {
  const cats = [
    {
      key:   'herramientas',
      label: '🔧 Herramientas técnicas',
      max:   35,
      color: 'var(--accent)',
    },
    {
      key:   'funcional',
      label: '📋 Palabras clave funcionales',
      max:   35,
      color: '#1d4ed8',
    },
    {
      key:   'perfil',
      label: '🎯 Alineación de perfil',
      max:   20,
      color: 'var(--warn)',
    },
    {
      key:   'claridad',
      label: '📐 Claridad y estructura',
      max:   10,
      color: '#6d28d9',
    },
  ];

  const rows = cats.map(cat => {
    const raw   = desglose[cat.key] ?? 0;
    const pct   = Math.min(100, Math.round((raw / cat.max) * 100));
    const id    = `bar-${cat.key}`;
    return `
      <div style="margin-bottom:14px;">
        <div class="flex justify-between items-center" style="margin-bottom:5px;">
          <span style="font-size:0.85rem;font-weight:500;color:var(--ink);">${cat.label}</span>
          <span class="syne" style="font-size:0.78rem;color:var(--muted);">${raw.toFixed(1)} / ${cat.max}</span>
        </div>
        <div class="progress-bg" style="height:10px;">
          <div
            id="${id}"
            class="progress-fill"
            style="background:${cat.color};width:0%;height:100%;border-radius:999px;transition:width 1s cubic-bezier(0.4,0,0.2,1);"
            data-target="${pct}"
          ></div>
        </div>
      </div>
    `;
  }).join('');

  desgloseDiv.innerHTML = `
    <div class="card p-6 md:p-8 fade-in stagger-4 mt-5" style="border-color:#e5e1d8;">
      <p class="section-title" style="color:#374151;margin-bottom:18px;">📊 Desglose por categoría</p>
      <p style="font-size:0.82rem;color:var(--muted);margin-bottom:18px;line-height:1.5;">
        Cada categoría aporta un peso distinto al puntaje global. Esto te ayuda a entender
        <strong>dónde mejorar</strong> aunque tengas buenas herramientas técnicas.
      </p>
      ${rows}
    </div>
  `;
  desgloseDiv.classList.remove('hidden');

  // Animate all bars after a short delay
  setTimeout(() => {
    cats.forEach(cat => {
      const el = document.getElementById(`bar-${cat.key}`);
      if (el) el.style.width = el.dataset.target + '%';
    });
  }, 200);
}

// ---- Render keyword badges ----
function renderPalabrasClave(keywords) {
  if (!keywords || !keywords.length) return;
  const chips = keywords.map(k => `<span class="kw-chip">${escapeHtml(k)}</span>`).join('');
  kwDiv.innerHTML = `
    <div class="section-kw fade-in stagger-5 mt-5">
      <p class="section-title" style="color:#374151;">🔑 Palabras clave que los sistemas ATS buscarán</p>
      <p style="font-size:0.85rem;color:var(--muted);margin-bottom:10px;">
        Asegúrate de que aparezcan <strong>exactamente</strong> en tu CV.
      </p>
      <div>${chips}</div>
    </div>
  `;
  kwDiv.classList.remove('hidden');
}

// ---- Render ATS explanation ----
function renderContextoAts(consejos) {
  const consejosHtml = (consejos && consejos.length)
    ? consejos.map(c => `
        <div class="result-list-item">
          <span class="emoji">🔍</span>
          <span style="font-size:0.9rem;line-height:1.6;">${c}</span>
        </div>`).join('')
    : '';

  atsDiv.innerHTML = `
    <div class="section-ats fade-in mt-5">
      <p class="section-title" style="color:var(--ats-text);">🤖 ¿Cómo funciona este análisis?</p>

      <p style="font-size:0.9rem;line-height:1.7;color:#374151;margin-bottom:14px;">
        MatchCV Lite compara tu hoja de vida con la oferta laboral usando dos métodos:
      </p>

      <div style="margin-bottom:14px;">
        <p style="font-size:0.9rem;line-height:1.65;color:#374151;margin-bottom:8px;">
          <strong>1️⃣ Similitud de palabras clave (TF-IDF):</strong> Detecta qué tan similares son
          los términos de tu CV con los de la vacante. Los sistemas ATS usan esta técnica
          para filtrar candidatos automáticamente.
        </p>
        <p style="font-size:0.9rem;line-height:1.65;color:#374151;margin-bottom:4px;">
          <strong>2️⃣ Reglas inteligentes:</strong> Evaluamos cuatro aspectos ponderados:
        </p>
        <ul style="font-size:0.88rem;line-height:1.7;color:#4b5563;padding-left:20px;list-style:disc;">
          <li>Herramientas técnicas (Python, SQL, Excel, Power BI…) — <strong>35%</strong></li>
          <li>Palabras clave funcionales (verbos + conceptos de dominio) — <strong>35%</strong></li>
          <li>Alineación de seniority e industria — <strong>20%</strong></li>
          <li>Claridad y estructura (fechas, logros cuantificables) — <strong>10%</strong></li>
        </ul>
      </div>

      <p style="font-size:0.88rem;line-height:1.65;color:#374151;margin-bottom:${consejosHtml ? '14px' : '10px'};">
        <strong>¿Por qué es útil?</strong> Hasta el <strong>75% de los CVs</strong> son descartados
        automáticamente por no incluir palabras clave exactas. Este análisis te ayuda a identificar
        esos filtros invisibles.
      </p>

      ${consejosHtml ? `<div>${consejosHtml}</div>` : ''}

      <p style="font-size:0.82rem;color:var(--muted);margin-top:14px;padding-top:12px;border-top:1px solid var(--ats-border);">
        💡 Los resultados son orientativos. Cada empresa usa su propio sistema de filtrado.
      </p>
    </div>
  `;
  atsDiv.classList.remove('hidden');
}

// ---- Copy analysis ----
function copiarAnalisis() {
  if (!ultimoResultado) return;
  const { encaje_global, nivel, aporta, brechas, recomendaciones, frase_final } = ultimoResultado;
  const lines = [
    '═══════════════════════════════════',
    '       ANÁLISIS MatchCV Lite',
    '═══════════════════════════════════',
    '',
    `Encaje global: ${encaje_global}% — ${nivel}`,
    '',
    '✅ LO QUE APORTAS',
    ...(aporta.length  ? aporta.map(a  => `  • ${a}`)               : ['  (sin aportes detectados)']),
    '',
    '⚠️ BRECHAS DETECTADAS',
    ...(brechas.length ? brechas.map(b => `  • ${b}`)               : ['  (sin brechas detectadas)']),
    '',
    '📝 RECOMENDACIONES',
    ...(recomendaciones.length ? recomendaciones.map((r,i) => `  ${i+1}. ${r}`) : ['  (sin recomendaciones)']),
    '',
    '───────────────────────────────────',
    frase_final,
    '───────────────────────────────────',
    '',
    'Generado por MatchCV Lite',
  ];
  navigator.clipboard.writeText(lines.join('\n'))
    .then(()  => showToast('✓ Análisis copiado'))
    .catch(()  => showToast('No se pudo copiar — inténtalo manualmente'));
}

function showToast(msg) {
  const t = document.getElementById('copyToast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

// ---- Helpers ----
function animateNumber(id, target, duration) {
  const el = document.getElementById(id);
  if (!el) return;
  const startTime = performance.now();
  function step(now) {
    const p = Math.min((now - startTime) / duration, 1);
    el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))) + '%';
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function showError(msg) {
  resultadoDiv.innerHTML = `
    <div class="card p-6 fade-in" style="border-color:#f5c2be;background:#fff5f5;">
      <div class="flex items-start gap-3">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2" style="flex-shrink:0;margin-top:3px;">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <div>
          <p class="syne font-bold" style="font-size:0.9rem;color:var(--danger);margin-bottom:4px;">Error</p>
          <p style="font-size:0.9rem;line-height:1.6;color:var(--ink);">${escapeHtml(msg)}</p>
        </div>
      </div>
    </div>
  `;
  resultadoDiv.classList.remove('hidden');
  resultadoDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// --- Survey ----
const surveyAnswers = {};

document.querySelectorAll('.pill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const q = btn.dataset.q;
        document.querySelectorAll(`.pill-btn[data-q="${q}"]`).forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        surveyAnswers[q] = btn.dataset.v;
    });
});

document.getElementById('enviarEncuesta').addEventListener('click', async () => {
    const btn = document.getElementById('enviarEncuesta');
    const sugerencia = document.getElementById('sugerenciaTexto')?.value?.trim() || '';
    
    btn.disabled = true;
    btn.textContent = 'Enviando...';
    
    // Construir los datos correctamente
    const datosEncuesta = {
        util: surveyAnswers['util'] || '',
        pago: surveyAnswers['pago'] || '',
        gratis: surveyAnswers['gratis'] || '',
        mejora: surveyAnswers['mejora'] || '',
        sugerencia: sugerencia
    };
    
    console.log('Enviando datos:', datosEncuesta); // Para depurar
    
    // URL de Apps Script (cambiala por la tuya)
    const FEEDBACK_URL = `${BACKEND_URL}/feedback`;
    
    try {
        const response = await fetch(FEEDBACK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(datosEncuesta)
        });
    
        const resultado = await response.json();
        console.log('Respuesta backend:', resultado);
    
    } catch (error) {
        console.error('Error al enviar feedback:', error);
    }
    
    // Mostrar mensaje de agradecimiento
    const encuestaDiv = document.getElementById('encuesta');
    encuestaDiv.innerHTML = `
        <div class="text-center py-12">
            <p style="font-size:2.4rem;margin-bottom:12px;">🙌</p>
            <p class="syne font-bold text-base">¡Gracias por tu ayuda!</p>
            <p style="font-size:0.9rem;color:var(--muted);margin-top:6px;line-height:1.5;">Tu feedback nos ayuda a mejorar MatchCV Lite.</p>
        </div>
    `;
});
