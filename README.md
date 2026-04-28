# MatchCV Lite

**Analiza el encaje de tu CV con cualquier oferta laboral — gratis, sin login, sin guardar datos.**

---

## Estructura

```
matchcv-lite/
├── backend/
│   ├── requirements.txt
│   ├── main.py
│   ├── analyzer.py
│   └── text_extractor.py
└── frontend/
    ├── index.html
    └── script.js
```

---

## Instalación y ejecución local

### 1. Requisitos previos
- Python 3.9 o superior
- pip

### 2. Instalar dependencias del backend

```bash
cd matchcv-lite/backend
pip install -r requirements.txt
```

### 3. Ejecutar el servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El API estará disponible en: `http://localhost:8000`  
Documentación automática: `http://localhost:8000/docs`

### 4. Abrir el frontend

Abre `frontend/index.html` directamente en tu navegador.

> **Nota:** `script.js` detecta automáticamente si está en localhost y apunta al backend en `http://localhost:8000`. No necesitas cambiar nada.

---

## Despliegue en producción

### Backend (Render o Railway)

1. Sube la carpeta `backend/` a un repositorio Git.
2. En **Render**:
   - Nuevo Web Service → conecta tu repo.
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Copia la URL pública que te asigne (ej: `https://matchcv-backend.onrender.com`).

### Frontend

Edita la primera línea de `script.js` y añade justo antes del código:

```js
const BACKEND_OVERRIDE = 'https://matchcv-backend.onrender.com';
```

O bien sube el frontend a **Netlify / Vercel / GitHub Pages** (son archivos estáticos).

---

## Endpoints del API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/analizar` | Recibe `file` (form) + `oferta_texto` (form). Devuelve análisis JSON. |
| `POST` | `/feedback` | Recibe JSON con respuestas de encuesta. Guarda en `feedback.json`. |

### Respuesta de `/analizar` (ejemplo)

```json
{
  "exito": true,
  "encaje_global": 68.4,
  "nivel": "Encaje medio",
  "aporta": ["Experiencia en tecnología", "Uso de herramientas: python, sql"],
  "brechas": ["Faltan palabras clave: docker, kubernetes"],
  "recomendaciones": ["Incluye 'docker' en tu sección de habilidades"],
  "frase_final": "⚠️ Aplica solo si haces estos cambios recomendados"
}
```

---

## Tecnologías

- **Backend:** Python, FastAPI, scikit-learn, PyPDF2, python-docx
- **Frontend:** HTML5, TailwindCSS (CDN), JavaScript Vanilla
- **Análisis:** TF-IDF cosine similarity + scoring ponderado por experiencia, herramientas, perfil y claridad

---

## Privacidad

- Los archivos y el texto de la oferta se procesan **en memoria** y **no se almacenan**.
- Solo se guarda el feedback de la encuesta (sin datos del CV ni de la oferta).
