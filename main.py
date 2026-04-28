import json
import logging
import os
import traceback
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from analyzer import analyze_cv
from text_extractor import extract_text_from_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="MatchCV Lite API", version="1.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _error(msg: str, status: int = 400) -> JSONResponse:
    logger.warning("Request error: %s", msg)
    return JSONResponse(content={"exito": False, "error": msg}, status_code=status)


@app.post("/analizar")
async def analizar(
    oferta_texto: str = Form(...),
    file: Optional[UploadFile] = File(None),
    cv_texto: Optional[str] = Form(None),
):
    # --- Validate offer ---
    if not oferta_texto or len(oferta_texto.strip()) < 20:
        return _error("La oferta laboral es demasiado corta (mínimo 20 caracteres).")

    cv_text: Optional[str] = None

    # --- Extract CV text ---
    try:
        if file and file.filename:
            filename = file.filename or "archivo"
            ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
            if ext not in {"pdf", "docx", "txt"}:
                return _error(f"Formato '.{ext}' no soportado. Sube un archivo PDF, DOCX o TXT.")

            try:
                file_bytes = await file.read()
            except Exception as e:
                return _error(f"No se pudo leer el archivo subido: {e}", 500)

            if len(file_bytes) == 0:
                return _error("El archivo subido está vacío.")
            if len(file_bytes) > MAX_FILE_SIZE:
                return _error("El archivo supera el límite de 5 MB.")

            try:
                cv_text = extract_text_from_file(file_bytes, filename)
            except RuntimeError as e:
                return _error(str(e), 422)
            except Exception as e:
                logger.error("Unexpected extraction error: %s", traceback.format_exc())
                return _error(
                    f"Error inesperado al leer el archivo '{filename}'. "
                    f"Tipo: {type(e).__name__}. Intenta con otro formato o pega el texto directamente.",
                    500,
                )

        elif cv_texto and len(cv_texto.strip()) >= 100:
            cv_text = cv_texto.strip()

        else:
            if cv_texto and len(cv_texto.strip()) < 100:
                return _error(
                    "El texto del CV pegado es demasiado corto (mínimo 100 caracteres). "
                    "Pega el contenido completo de tu hoja de vida."
                )
            return _error(
                "Debes subir un archivo CV (PDF/DOCX/TXT) "
                "o pegar el texto de tu hoja de vida (mínimo 100 caracteres)."
            )

    except JSONResponse:
        raise
    except Exception as e:
        logger.error("Unexpected error in CV extraction: %s", traceback.format_exc())
        return _error(f"Error inesperado procesando el CV: {type(e).__name__} — {e}", 500)

    # --- Run analysis ---
    try:
        resultado = analyze_cv(cv_text, oferta_texto)
        return {"exito": True, **resultado}

    except ValueError as e:
        logger.error("ValueError in analyze_cv: %s", e)
        return _error(f"Error de análisis (datos inválidos): {e}", 422)

    except Exception as e:
        logger.error("Unexpected error in analyze_cv: %s", traceback.format_exc())
        return _error(
            f"Error inesperado durante el análisis: {type(e).__name__}. "
            "El equipo ha sido notificado. Inténtalo de nuevo en unos segundos.",
            500,
        )


@app.post("/feedback")
async def feedback(data: dict):
    try:
        entry = {"timestamp": datetime.utcnow().isoformat(), **data}
        feedback_path = os.path.join(os.path.dirname(__file__), "feedback.json")
        entries: list = []
        if os.path.exists(feedback_path):
            try:
                with open(feedback_path, "r", encoding="utf-8") as f:
                    entries = json.load(f)
                    if not isinstance(entries, list):
                        entries = []
            except (json.JSONDecodeError, OSError):
                entries = []
        entries.append(entry)
        with open(feedback_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        return {"mensaje": "Gracias por tu ayuda"}
    except Exception as e:
        logger.warning("Feedback save failed: %s", e)
        return {"mensaje": "Gracias por tu ayuda", "advertencia": str(e)}


@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}
