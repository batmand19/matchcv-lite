import re
import unicodedata

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN_OK = True
except ImportError:
    _SKLEARN_OK = False


STOP_WORDS_ES = [
    'que', 'de', 'la', 'el', 'en', 'y', 'a', 'los', 'se', 'del',
    'las', 'un', 'por', 'con', 'una', 'para', 'es', 'al', 'lo',
    'como', 'mas', 'pero', 'sus', 'le', 'ya', 'cuando'
]

# SAS is excluded from base list — added dynamically only if offer mentions it
HERRAMIENTAS_BASE = [
    'python', 'sql', 'excel', 'powerbi', 'tableau', 'looker', 'qlik',
    'azure', 'aws', 'gcp', 'git', 'docker', 'kubernetes', 'airflow',
    'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
    'spss', 'stata', 'matlab', 'r', 'java', 'scala', 'javascript',
    'kpi', 'dashboard', 'analisis_datos', 'planeacion_financiera', 'automatizacion'
]

_BLOQUES_IRRELEVANTES = [
    r'acerca del empleo',
    r'nuestro equipo de talento humano',
    r'atrevete a crecer',
    r'postularte',
    r'confidencial',
    r'igualdad de oportunidades',
    r'creemos en el poder',
    r'conectar personas',
    r'impulsar el crecimiento',
    r'abrir caminos',
]

# Used for profile-alignment scoring (section 4)
_VERBOS_ACCION = [
    'analizar', 'validar', 'automatizar', 'transformar', 'crear', 'medir',
    'gestionar', 'disenar', 'implementar', 'desarrollar', 'coordinar',
    'reportar', 'optimizar', 'monitorear', 'construir', 'extraer',
    'procesar', 'visualizar', 'modelar', 'liderar', 'controlar'
]

# Used for functional keyword analysis (section 2 / brechas)
_VERBOS_FUNCIONALES = [
    'automatizar', 'transformar', 'analizar', 'procesar', 'construir',
    'desarrollar', 'medir', 'reportar', 'gestionar', 'coordinar',
    'implementar', 'optimizar', 'extraer', 'modelar', 'visualizar',
    'validar', 'liderar', 'controlar', 'monitorear', 'disenar'
]

_SUSTANTIVOS_CLAVE = [
    'forecast', 'presupuesto', 'kpi', 'dashboard', 'reporte', 'reportes',
    'flujo_de_caja', 'cartera', 'tesoreria', 'facturacion',
    'modelos_predictivos', 'modelo_predictivo', 'planeacion_financiera',
    'analisis_datos', 'automatizacion', 'inteligencia_de_negocios',
    'cierre_financiero', 'variacion', 'ejecucion_presupuestal',
    'indicadores', 'metricas', 'seguimiento', 'conciliacion',
    'proyeccion', 'pipeline', 'etl', 'data_warehouse', 'bi'
]

_TITULOS_VACANTE = [
    ('analista de datos',         'Analista de Datos'),
    ('analisis_datos',            'Analista de Datos'),
    ('data analyst',              'Data Analyst'),
    ('planeacion_financiera',     'Analista de Planeación Financiera'),
    ('planeacion financiera',     'Analista de Planeación Financiera'),
    ('financial planning',        'Financial Planning Analyst'),
    ('cientifico de datos',       'Científico de Datos'),
    ('data scientist',            'Data Scientist'),
    ('ingeniero de datos',        'Ingeniero de Datos'),
    ('data engineer',             'Data Engineer'),
    ('desarrollador',             'Desarrollador de Software'),
    ('developer',                 'Software Developer'),
    ('analista de bi',            'Analista de BI'),
    ('business intelligence',     'Business Intelligence Analyst'),
    ('analista financiero',       'Analista Financiero'),
    ('project manager',           'Project Manager'),
    ('gerente de proyecto',       'Gerente de Proyecto'),
    ('comercio exterior',         'Analista de Comercio Exterior'),
    ('supply chain',              'Analista de Supply Chain'),
    ('logistica',                 'Analista de Logística'),
    ('recursos humanos',          'Analista de Recursos Humanos'),
    ('marketing digital',         'Analista de Marketing Digital'),
]

_SINONIMOS = [
    (['power bi', 'powerbi'],                                    'powerbi'),
    (['hojas de calculo', 'hoja de calculo', 'excel'],           'excel'),
    (['consultas sql', 'bases de datos', 'sql'],                  'sql'),
    (['programacion python', 'python'],                           'python'),
    (['indicadores', 'metricas', 'kpi'],                          'kpi'),
    (['automatizar procesos', 'automatizacion', 'automatizar'],   'automatizacion'),
    (['panel de control', 'tablero', 'dashboard'],                'dashboard'),
    (['planificacion financiera', 'analisis financiero',
      'planeacion financiera'],                                    'planeacion_financiera'),
    (['data analysis', 'data analytics', 'analisis de datos'],    'analisis_datos'),
    (['flujo de caja'],                                            'flujo_de_caja'),
    (['modelos predictivos', 'modelo predictivo'],                 'modelos_predictivos'),
    (['inteligencia de negocios', 'business intelligence'],        'inteligencia_de_negocios'),
    (['cierre financiero'],                                        'cierre_financiero'),
    (['ejecucion presupuestal'],                                   'ejecucion_presupuestal'),
    (['data warehouse'],                                           'data_warehouse'),
]

_DESGLOSE_VACIO = {"herramientas": 0.0, "funcional": 0.0, "perfil": 0.0, "claridad": 0.0}

_RESULTADO_TEXTO_CORTO = {
    "encaje_global":         0.0,
    "nivel":                 "Texto insuficiente",
    "aporta":                ["No se pudo analizar correctamente"],
    "brechas":               ["El texto proporcionado es muy corto"],
    "recomendaciones":       ["Asegúrate de pegar la oferta completa (mínimo 100 caracteres) y tu CV completo"],
    "frase_final":           "❌ No se pudo realizar el análisis. Revisa que hayas pegado todo el contenido.",
    "contexto_ats":          [],
    "palabras_clave_oferta": [],
    "desglose":              _DESGLOSE_VACIO,
}

_DEFAULT_RESULT = {
    "encaje_global":         0.0,
    "nivel":                 "Encaje bajo",
    "aporta":                [],
    "brechas":               ["No se pudo extraer texto suficiente del CV o la oferta para analizar."],
    "recomendaciones":       ["Verifica que el archivo CV tenga texto extraíble y que la oferta sea completa."],
    "frase_final":           "❌ No se pudo completar el análisis. Revisa los archivos e inténtalo de nuevo.",
    "contexto_ats":          [],
    "palabras_clave_oferta": [],
    "desglose":              _DESGLOSE_VACIO,
}

_H_DISPLAY_MAP = {
    'powerbi':               'Power BI',
    'analisis_datos':        'Análisis de Datos',
    'planeacion_financiera': 'Planeación Financiera',
    'automatizacion':        'Automatización',
    'kpi':                   'KPI / Indicadores',
    'dashboard':             'Dashboard',
    'scikit-learn':          'Scikit-learn',
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def filtrar_oferta(texto: str) -> str:
    """Removes boilerplate / sign-off blocks from job offer text."""
    if not texto:
        return texto
    for pat in [r'\bSaludos[,\.]', r'\bAtentamente[,\.]', r'\bEquipo de\b']:
        m = re.search(pat, texto, re.IGNORECASE)
        if m:
            texto = texto[:m.start()]
            break
    lineas = texto.split('\n')
    limpias = []
    for linea in lineas:
        norm = _preprocess_line(linea)
        if not any(re.search(p, norm) for p in _BLOQUES_IRRELEVANTES):
            limpias.append(linea)
    return '\n'.join(limpias).strip()


limpiar_oferta = filtrar_oferta  # backward-compat alias


def normalizar_terminos(texto: str) -> str:
    """Replaces synonym variants with canonical tokens."""
    t = texto.lower()
    t = unicodedata.normalize('NFKD', t)
    t = ''.join(c for c in t if not unicodedata.combining(c))
    for variantes, canonico in _SINONIMOS:
        for variante in sorted(variantes, key=len, reverse=True):
            t = re.sub(r'\b' + re.escape(variante) + r'\b', canonico, t)
    return t


def herramientas_en_oferta(oferta_clean: str) -> list:
    """Returns only tools that explicitly appear in the (normalised) offer text."""
    lista = list(HERRAMIENTAS_BASE)
    if 'sas' in oferta_clean:
        lista.append('sas')
    return [h for h in lista if h in oferta_clean]


def h_display(h: str) -> str:
    """Human-readable label for a canonical tool token."""
    return _H_DISPLAY_MAP.get(h, h.upper() if len(h) <= 4 else h.title())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _preprocess_line(linea: str) -> str:
    t = linea.lower()
    t = unicodedata.normalize('NFKD', t)
    t = ''.join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def _normalizar(texto: str) -> str:
    texto = normalizar_terminos(texto)
    texto = re.sub(r'[^a-z0-9_\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def _contar_logros(texto_clean: str) -> int:
    """Improved quantifiable-achievement detection."""
    patrones = [
        r'\d+\s*(?:%|por ciento)',
        r'\d+\s*(?:mil|millones)',
        r'\+\s*\d+',
        r'-\s*\d+\s*(?:%|horas|dias|semanas)',
        r'\baumento\b', r'\baumente\b', r'\baumentar\b',
        r'\breduccion\b', r'\breduje\b', r'\breducir\b',
        r'\bincremento\b', r'\bincremente\b', r'\bincrementar\b',
        r'\bdisminucion\b', r'\bdisminuir\b',
        r'\boptimizacion\b', r'\boptimice\b', r'\boptimizar\b',
        r'\bahorro\b', r'\bahorrar\b',
        r'\beficiencia\b',
        r'\bmejora\b', r'\bmejore\b', r'\bmejorar\b',
        r'\bcrecimiento\b',
        r'\blogramos\b', r'\blogre\b', r'\blograr\b',
    ]
    return sum(len(re.findall(p, texto_clean)) for p in patrones)


def _detectar_funcion_principal(oferta_clean: str) -> str:
    funciones = [
        ('analisis_datos',            'análisis de datos'),
        ('planeacion_financiera',     'planeación financiera'),
        ('automatizacion',            'automatización'),
        ('gestion de proyectos',      'gestión de proyectos'),
        ('desarrollo de software',    'desarrollo de software'),
        ('inteligencia_de_negocios',  'inteligencia de negocios'),
        ('ciencia de datos',          'ciencia de datos'),
        ('administracion',            'administración'),
        ('contabilidad',              'contabilidad'),
    ]
    for clave, display in funciones:
        if clave in oferta_clean:
            return display
    return 'las funciones del cargo'


def _detectar_titulo_vacante(oferta_clean: str):
    for clave, display in _TITULOS_VACANTE:
        clave_norm = _normalizar(clave)
        if clave_norm in oferta_clean:
            return clave_norm, display
    return None, None


def _extraer_palabras_clave_oferta(oferta_clean: str, n: int = 10) -> list:
    """Top-n most frequent meaningful words from the normalised offer."""
    tokens = [w for w in oferta_clean.split() if w not in STOP_WORDS_ES and len(w) > 2]
    if not tokens:
        return []
    freq: dict = {}
    for t in tokens:
        if not re.match(r'^\d+$', t):
            freq[t] = freq.get(t, 0) + 1
    top = sorted(freq.items(), key=lambda x: -x[1])
    return [w for w, _ in top[:n]]


def _calcular_freq_oferta(oferta_clean: str) -> dict:
    """Word frequency map for the offer — used in brecha/rec logic."""
    freq: dict = {}
    for w in oferta_clean.split():
        if w not in STOP_WORDS_ES and len(w) > 2 and not re.match(r'^\d+$', w):
            freq[w] = freq.get(w, 0) + 1
    return freq


def _extraer_tareas_principales(oferta_clean: str) -> list:
    """Extract 2-3 main task phrases from the offer for low-match recommendation."""
    patrones_tareas = [
        (r'\bautomatizar\b',  'automatización de procesos'),
        (r'\banalizar\b',     'análisis de datos'),
        (r'\bconstruir\b',    'construcción de reportes / modelos'),
        (r'\bdesarrollar\b',  'desarrollo de modelos o dashboards'),
        (r'\bgestionar\b',    'gestión de información'),
        (r'\breportar\b',     'generación de reportes ejecutivos'),
        (r'\boptimizar\b',    'optimización de procesos'),
        (r'\bmodelar\b',      'modelación financiera o de datos'),
        (r'\bvisualizar\b',   'visualización de datos'),
        (r'\bprocesar\b',     'procesamiento de datos'),
        (r'\bimplementar\b',  'implementación de soluciones'),
        (r'\bforecast\b',     'planeación y forecast financiero'),
        (r'\bpresupuesto\b',  'elaboración de presupuestos'),
        (r'\betl\b',          'procesos ETL de datos'),
    ]
    tareas = []
    for pat, desc in patrones_tareas:
        if re.search(pat, oferta_clean):
            tareas.append(desc)
        if len(tareas) >= 3:
            break
    return tareas if tareas else ['análisis de datos', 'generación de reportes']


def _analizar_palabras_funcionales(cv_clean: str, oferta_clean: str) -> dict:
    """
    Analyses functional verb and noun overlap between CV and offer.
    Returns a dict with verb/noun lists and an overlap ratio (0-1).
    """
    verbos_oferta    = [v for v in _VERBOS_FUNCIONALES if v in oferta_clean]
    verbos_cv        = [v for v in _VERBOS_FUNCIONALES if v in cv_clean]
    verbos_faltantes = [v for v in verbos_oferta if v not in verbos_cv]

    sustantivos_oferta    = [s for s in _SUSTANTIVOS_CLAVE if s in oferta_clean]
    sustantivos_cv        = [s for s in _SUSTANTIVOS_CLAVE if s in cv_clean]
    sustantivos_faltantes = [s for s in sustantivos_oferta if s not in sustantivos_cv]

    total = len(verbos_oferta) + len(sustantivos_oferta)
    match = (len(verbos_oferta) - len(verbos_faltantes)) + \
            (len(sustantivos_oferta) - len(sustantivos_faltantes))
    ratio = (match / total) if total > 0 else 0.5   # neutral when nothing detected

    return {
        "verbos_oferta":          verbos_oferta,
        "verbos_cv":              verbos_cv,
        "verbos_faltantes":       verbos_faltantes,
        "sustantivos_oferta":     sustantivos_oferta,
        "sustantivos_cv":         sustantivos_cv,
        "sustantivos_faltantes":  sustantivos_faltantes,
        "ratio":                  ratio,
    }


def _generar_contexto_ats(
    puntaje_tools_ratio: float,
    palabras_cv_count: int,
    num_logros: int,
    tiene_fechas: bool,
    tiene_vinetas: bool,
) -> list:
    consejos = []
    if puntaje_tools_ratio < 0.50:
        consejos.append(
            "En empresas con filtros automáticos, las herramientas técnicas son un filtro "
            "eliminatorio. Incluye las palabras <strong>exactas</strong> de la vacante "
            "(ej: 'Power BI', 'Excel avanzado') para pasar el primer filtro."
        )
    if palabras_cv_count > 800:
        consejos.append(
            "Los sistemas ATS suelen priorizar CVs concisos (500–700 palabras). "
            "Extenderte demasiado puede hacer que información clave sea ignorada."
        )
    if num_logros < 2:
        consejos.append(
            "Muchos sistemas buscan patrones numéricos (%, $, cantidades) como evidencia "
            "de impacto. Agregar métricas mejora significativamente tu puntuación automática."
        )
    if not tiene_fechas:
        consejos.append(
            "La mayoría de ATS requieren fechas claras (mes/año) para verificar antigüedad. "
            "Sin ellas, tu CV puede ser penalizado automáticamente."
        )
    if not tiene_vinetas:
        consejos.append(
            "Los filtros automáticos extraen secciones por títulos estandarizados "
            "('Experiencia', 'Educación', 'Habilidades'). Usa estos encabezados exactos "
            "para mejorar la legibilidad del sistema."
        )
    if not consejos:
        consejos.append(
            "Tu CV tiene buena estructura para filtros automáticos. "
            "Enfócate en ajustar palabras clave específicas de cada vacante antes de postular."
        )
    return consejos


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyze_cv(cv_text: str, oferta_text: str) -> dict:
    """Full CV-vs-offer analysis. Never raises — returns _DEFAULT_RESULT on error."""
    try:
        return _analyze_cv_inner(cv_text, oferta_text)
    except Exception as exc:
        result = dict(_DEFAULT_RESULT)
        result["brechas"] = [f"Error interno durante el análisis: {type(exc).__name__} — {exc}"]
        return result


def _analyze_cv_inner(cv_text: str, oferta_text: str) -> dict:
    cv_text     = (cv_text     or "").strip()
    oferta_text = (oferta_text or "").strip()

    # Short-text guard
    if len(cv_text) < 100 or len(oferta_text) < 100:
        result = dict(_RESULTADO_TEXTO_CORTO)
        if len(cv_text) < 100 and len(oferta_text) >= 100:
            result["brechas"] = ["El texto del CV es muy corto (mínimo 100 caracteres)."]
        elif len(oferta_text) < 100 and len(cv_text) >= 100:
            result["brechas"] = ["El texto de la oferta es muy corto (mínimo 100 caracteres)."]
        return result

    # Normalise & clean
    cv_norm     = normalizar_terminos(cv_text)
    oferta_norm = filtrar_oferta(normalizar_terminos(oferta_text))
    if not oferta_norm.strip():
        oferta_norm = normalizar_terminos(oferta_text)

    cv_clean     = _normalizar(cv_norm)
    oferta_clean = _normalizar(oferta_norm)

    if not cv_clean or not oferta_clean:
        return dict(_DEFAULT_RESULT)

    # -----------------------------------------------------------------------
    # 1. TF-IDF cosine similarity (contributes to base score)
    # -----------------------------------------------------------------------
    encaje_global_base = 0.0
    if _SKLEARN_OK:
        try:
            vectorizer   = TfidfVectorizer(stop_words=STOP_WORDS_ES, max_features=500)
            tfidf_matrix = vectorizer.fit_transform([cv_clean, oferta_clean])
            encaje_global_base = float(
                cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            ) * 100
        except Exception:
            encaje_global_base = 0.0

    # -----------------------------------------------------------------------
    # 2. Palabras clave funcionales (35%) — verb + domain-noun overlap
    # -----------------------------------------------------------------------
    func                  = _analizar_palabras_funcionales(cv_clean, oferta_clean)
    puntaje_funcional     = func["ratio"] * 35

    # Raw keyword overlap — used for brecha priority-1 check
    palabras_oferta = set(oferta_clean.split()) - set(STOP_WORDS_ES)
    palabras_cv     = set(cv_clean.split())
    coincidencia_kw = (len(palabras_oferta & palabras_cv) / len(palabras_oferta)) \
                      if palabras_oferta else 0.0

    # Offer word-frequency map — built once, reused in brechas/recos
    freq_oferta = _calcular_freq_oferta(oferta_clean)

    # -----------------------------------------------------------------------
    # 3. Herramientas técnicas (35%)
    # -----------------------------------------------------------------------
    tools_oferta = herramientas_en_oferta(oferta_clean)
    tools_cv     = [h for h in (HERRAMIENTAS_BASE + (['sas'] if 'sas' in oferta_clean else []))
                    if h in cv_clean]

    if tools_oferta:
        tools_coincidentes  = [h for h in tools_cv if h in tools_oferta]
        tools_faltantes     = [h for h in tools_oferta if h not in tools_cv]
        ratio_tools         = len(tools_coincidentes) / len(tools_oferta)
        puntaje_tools       = ratio_tools * 35
        puntaje_tools_ratio = ratio_tools
    else:
        tools_coincidentes  = tools_cv
        tools_faltantes     = []
        puntaje_tools       = 35 * 0.70
        puntaje_tools_ratio = 0.70

    tools_coincidentes_disp = [h_display(h) for h in tools_coincidentes]
    tools_faltantes_disp    = [h_display(h) for h in tools_faltantes]

    # -----------------------------------------------------------------------
    # 4. Alineación perfil (20%)
    # -----------------------------------------------------------------------
    seniority_patterns = ['junior', 'semi senior', 'semisenior', 'senior', 'lead']
    seniority_cv       = next((s for s in seniority_patterns if s in cv_clean), None)
    seniority_oferta   = next((s for s in seniority_patterns if s in oferta_clean), None)
    puntaje_seniority  = 15 if (seniority_cv and seniority_oferta and seniority_cv == seniority_oferta) else 0

    verbos_oferta_set  = {v for v in _VERBOS_ACCION if v in oferta_clean}
    verbos_cv_set      = {v for v in _VERBOS_ACCION if v in cv_clean}
    verbos_comunes     = verbos_oferta_set & verbos_cv_set
    puntaje_perfil     = puntaje_seniority + min(5, len(verbos_comunes))

    # -----------------------------------------------------------------------
    # 5. Claridad y estructura (10%)
    # -----------------------------------------------------------------------
    tiene_fechas       = bool(re.search(r'\d{4}', cv_text))
    num_logros         = _contar_logros(cv_clean)
    tiene_logros       = num_logros >= 1
    logros_suficientes = num_logros >= 3
    palabras_cv_count  = len(cv_text.split())
    tiene_vinetas      = bool(re.search(r'[-•·*]', cv_text))

    puntaje_claridad = 0
    if tiene_fechas:               puntaje_claridad += 3
    if tiene_logros:               puntaje_claridad += 3
    if logros_suficientes:         puntaje_claridad += 1
    if palabras_cv_count <= 1000:  puntaje_claridad += 2
    if tiene_vinetas:              puntaje_claridad += 1

    # -----------------------------------------------------------------------
    # Composite score
    # -----------------------------------------------------------------------
    encaje_global = round(min(100.0, max(0.0,
        encaje_global_base * 0.35
        + puntaje_funcional  * 0.35
        + puntaje_tools      * 0.35
        + puntaje_perfil     * 0.20
        + puntaje_claridad   * 0.10
    )), 1)

    nivel = (
        "Buen encaje"  if encaje_global >= 70 else
        "Encaje medio" if encaje_global >= 40 else
        "Encaje bajo"
    )

    # -----------------------------------------------------------------------
    # Aportes
    # -----------------------------------------------------------------------
    aportes = []
    if tools_coincidentes_disp:
        aportes.append(f"Manejo de herramientas requeridas: {', '.join(tools_coincidentes_disp[:3])}")
    if verbos_comunes:
        aportes.append(f"Experiencia en funciones clave: {', '.join(list(verbos_comunes)[:2])}")
    if seniority_cv and seniority_oferta and seniority_cv == seniority_oferta:
        aportes.append(f"Nivel de seniority alineado ({seniority_cv})")
    if not aportes:
        if palabras_cv_count > 100: aportes.append("CV con contenido suficiente para evaluar")
        if tiene_fechas:             aportes.append("Historial laboral con fechas visibles")
        if tiene_logros:             aportes.append("Incluye logros o resultados medibles")
    aportes = aportes[:3]

    # -----------------------------------------------------------------------
    # Brechas — priority-based logic
    # -----------------------------------------------------------------------
    brechas = []

    # Priority 1: low keyword alignment
    if encaje_global < 50 and coincidencia_kw < 0.30:
        palabras_faltantes_cv = sorted(
            [w for w in palabras_oferta
             if w not in palabras_cv and len(w) > 3 and not re.match(r'^\d+$', w)],
            key=lambda w: -freq_oferta.get(w, 0)
        )[:5]
        if palabras_faltantes_cv:
            brechas.append(
                "Tu CV no menciona términos clave que la vacante busca repetidamente"
            )

    # Priority 2: tools from offer missing in CV
    if tools_faltantes_disp and len(brechas) < 3:
        brechas.append(
            f"Herramientas de la oferta no detectadas en tu CV: {', '.join(tools_faltantes_disp[:4])}"
        )

    # Priority 3: missing functional verbs
    verbos_faltantes = func["verbos_faltantes"]
    if verbos_faltantes and len(brechas) < 3:
        sample = ', '.join(f"'{v}'" for v in verbos_faltantes[:3])
        brechas.append(
            f"Faltan verbos de acción relevantes como {sample} que aparecen en la oferta"
        )

    # Priority 4: missing domain nouns/concepts
    sustantivos_faltantes = func["sustantivos_faltantes"]
    if sustantivos_faltantes and len(brechas) < 3:
        sf_display = [s.replace('_', ' ').title() for s in sustantivos_faltantes[:3]]
        brechas.append(
            f"No se mencionan conceptos clave solicitados: {', '.join(sf_display)}"
        )

    # Priority 5: quantifiable achievements
    if len(brechas) < 3:
        if not tiene_logros:
            brechas.append("No se detectaron logros cuantificables (números, porcentajes, resultados)")
        elif not logros_suficientes:
            brechas.append("Pocos logros cuantificables — agrega más evidencia concreta")

    # Priority 6: dates
    if not tiene_fechas and len(brechas) < 3:
        brechas.append("No se detectaron fechas en la experiencia laboral")

    # Fallback: force at least one brecha when score is low but nothing fired
    if not brechas and encaje_global < 40:
        brechas.append(
            "El perfil general no se alinea con lo que busca la vacante. "
            "Revisa la sección 'Palabras clave que los sistemas ATS buscarán' y ajusta tu CV"
        )

    brechas = brechas[:3]

    # -----------------------------------------------------------------------
    # Recomendaciones
    # -----------------------------------------------------------------------
    funcion_principal            = _detectar_funcion_principal(oferta_clean)
    titulo_clave, titulo_display = _detectar_titulo_vacante(oferta_clean)

    recomendaciones = []

    # Rec 1: keyword gap (only when relevant)
    if encaje_global < 50 and coincidencia_kw < 0.30:
        palabras_faltantes_cv = sorted(
            [w for w in palabras_oferta
             if w not in palabras_cv and len(w) > 3 and not re.match(r'^\d+$', w)],
            key=lambda w: -freq_oferta.get(w, 0)
        )[:5]
        if palabras_faltantes_cv:
            recomendaciones.append(
                f"Agrega estas palabras clave a tu experiencia o perfil: "
                f"{', '.join(palabras_faltantes_cv)}"
            )

    # Rec 2: dates
    if not tiene_fechas:
        recomendaciones.append("Asegúrate de incluir fechas (mes/año) en cada experiencia laboral")

    # Rec 3: quantifiable achievements — specific example when none found
    if num_logros < 3:
        if not tiene_logros:
            recomendaciones.append(
                "Agrega frases como 'Automaticé 5 reportes financieros reduciendo "
                "el tiempo de generación en 40%'"
            )
        else:
            recomendaciones.append("Agrega al menos 3 logros medibles con números o porcentajes")

    # Rec 4: tools — only from the offer
    for h in tools_faltantes_disp[:2]:
        recomendaciones.append(f"Incluye '{h}' en tu sección de habilidades técnicas")

    # Rec 5: CV length
    if palabras_cv_count > 800:
        recomendaciones.append("Reduce tu CV a 500-700 palabras, elimina texto descriptivo genérico")

    # Rec 6: no tools section at all
    if not tools_cv:
        recomendaciones.append("Crea una sección 'Habilidades Técnicas' con herramientas y tecnologías")

    # Rec 7: title alignment
    if titulo_clave and titulo_clave not in cv_clean:
        recomendaciones.append(
            f"Incluye el título de la vacante o sus variantes (ej: '{titulo_display}') "
            f"en tu perfil o resumen profesional"
        )

    # Rec 8: low-match specific — tasks from offer
    if encaje_global < 45:
        tareas     = _extraer_tareas_principales(oferta_clean)
        tareas_str = ', '.join(f'"{t}"' for t in tareas)
        recomendaciones.append(
            f"Tu perfil tiene herramientas adecuadas, pero los logros que describes "
            f"no coinciden con las funciones principales de esta vacante. "
            f"Ajusta tu experiencia para reflejar tareas como: {tareas_str}"
        )

    recomendaciones = recomendaciones[:5]

    # -----------------------------------------------------------------------
    # Frase final
    # -----------------------------------------------------------------------
    if encaje_global >= 70:
        frase_final = "✔️ Buen match. Con los ajustes sugeridos, tienes alta probabilidad de pasar filtros automáticos."
    elif encaje_global >= 40:
        frase_final = "⚠️ Match medio. Aplica SOLO si realizas los cambios recomendados. Sin ajustes, podrías ser filtrado automáticamente."
    else:
        frase_final = "❌ Match bajo. En sistemas ATS reales, este CV probablemente sería descartado. Prioriza vacantes donde tu perfil coincida más."

    contexto_ats = _generar_contexto_ats(
        puntaje_tools_ratio=puntaje_tools_ratio,
        palabras_cv_count=palabras_cv_count,
        num_logros=num_logros,
        tiene_fechas=tiene_fechas,
        tiene_vinetas=tiene_vinetas,
    )

    palabras_clave_oferta = _extraer_palabras_clave_oferta(oferta_clean, n=10)

    # Desglose for frontend category progress bars (absolute points, max shown alongside)
    desglose = {
        "herramientas": round(puntaje_tools, 1),     # out of 35
        "funcional":    round(puntaje_funcional, 1),  # out of 35
        "perfil":       round(puntaje_perfil, 1),     # out of 20
        "claridad":     round(puntaje_claridad, 1),   # out of 10
    }

    return {
        "encaje_global":         encaje_global,
        "nivel":                 nivel,
        "aporta":                aportes,
        "brechas":               brechas,
        "recomendaciones":       recomendaciones,
        "frase_final":           frase_final,
        "contexto_ats":          contexto_ats,
        "palabras_clave_oferta": palabras_clave_oferta,
        "desglose":              desglose,
    }
