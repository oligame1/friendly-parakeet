"""Simple FastAPI web interface for Friendly Parakeet."""

from __future__ import annotations

import os
from html import escape
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from .agent import Agent, AgentAnswer
from .gemini_client import GeminiClient


def _create_app() -> FastAPI:
    app = FastAPI(
        title="Friendly Parakeet",
        description="Analyse interactive de devis PDF avec Gemini",
        version="0.1.0",
    )

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return _render_page()

    @app.post("/analyze", response_class=HTMLResponse)
    async def analyze(
        pdf: UploadFile = File(...),
        question: str = Form(...),
        section: Optional[str] = Form(None),
        top_k: int = Form(4),
        chunk_size: int = Form(1100),
        overlap: int = Form(200),
        model: str = Form("models/gemini-pro"),
    ) -> HTMLResponse:
        section_value = (section or "").strip() or None
        form_defaults = {
            "question": question,
            "section": section or "",
            "top_k": str(top_k),
            "chunk_size": str(chunk_size),
            "overlap": str(overlap),
            "model": model,
        }
        try:
            answers = await _compute_answers(
                upload=pdf,
                question=question.strip(),
                section=section_value,
                top_k=top_k,
                chunk_size=chunk_size,
                overlap=overlap,
                model=model,
            )
        except Exception as exc:  # pragma: no cover - surfaced in UI
            return HTMLResponse(
                content=_render_page(error=str(exc), form_defaults=form_defaults),
                status_code=500,
            )
        return HTMLResponse(
            content=_render_page(answers=answers, form_defaults=form_defaults)
        )

    @app.post("/api/analyze")
    async def api_analyze(
        pdf: UploadFile = File(...),
        question: str = Form(...),
        section: Optional[str] = Form(None),
        top_k: int = Form(4),
        chunk_size: int = Form(1100),
        overlap: int = Form(200),
        model: str = Form("models/gemini-pro"),
    ) -> JSONResponse:
        section_value = (section or "").strip() or None
        try:
            answers = await _compute_answers(
                upload=pdf,
                question=question.strip(),
                section=section_value,
                top_k=top_k,
                chunk_size=chunk_size,
                overlap=overlap,
                model=model,
            )
        except Exception as exc:  # pragma: no cover - API error path
            return JSONResponse(
                status_code=500,
                content={"error": str(exc)},
            )
        payload = {
            "answers": [
                {
                    "project": answer.project,
                    "answer": answer.answer,
                    "confidence": answer.confidence,
                    "sources": [
                        {
                            "page_number": source.page_number,
                            "score": source.score,
                            "excerpt": source.excerpt,
                        }
                        for source in answer.sources
                    ],
                }
                for answer in answers
            ]
        }
        return JSONResponse(content=payload)

    return app


async def _compute_answers(
    *,
    upload: UploadFile,
    question: str,
    section: Optional[str],
    top_k: int,
    chunk_size: int,
    overlap: int,
    model: str,
) -> List[AgentAnswer]:
    pdf_path = await _save_upload(upload)
    try:
        gemini = GeminiClient(model=model)
        agent = Agent.from_pdf(
            str(pdf_path),
            section=section,
            chunk_size=chunk_size,
            overlap=overlap,
            gemini=gemini,
        )
        return agent.answer(question, top_k=top_k)
    finally:
        try:
            pdf_path.unlink()
        except OSError:
            pass


async def _save_upload(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "document.pdf").suffix or ".pdf"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        content = await upload.read()
        tmp_file.write(content)
        saved_path = Path(tmp_file.name)
    upload.file.seek(0)
    return saved_path


def _render_page(
    *,
    answers: Optional[List[AgentAnswer]] = None,
    error: Optional[str] = None,
    form_defaults: Optional[Dict[str, str]] = None,
) -> str:
    form_defaults = form_defaults or {}
    question_value = escape(form_defaults.get("question", ""))
    section_value = escape(form_defaults.get("section", ""))
    top_k_value = escape(form_defaults.get("top_k", "4"))
    chunk_size_value = escape(form_defaults.get("chunk_size", "1100"))
    overlap_value = escape(form_defaults.get("overlap", "200"))
    model_value = escape(form_defaults.get("model", "models/gemini-pro"))

    message_block = ""
    if error:
        message_block = f"<div class=\"alert error\">{escape(error)}</div>"

    results_block = ""
    if answers:
        rows = []
        for answer in answers:
            sources_list = "".join(
                f"<li>Page {escape(str(source.page_number))} (score {source.score:.2f})</li>"
                for source in answer.sources
            ) or "<li>No source found</li>"
            rows.append(
                "<section class=\"card\">"
                f"<h3>{escape(answer.project)}</h3>"
                f"<p><strong>Confidence:</strong> {answer.confidence:.2f}</p>"
                f"<p>{_format_answer(answer.answer)}</p>"
                f"<details><summary>Sources</summary><ul>{sources_list}</ul></details>"
                "</section>"
            )
        results_block = "<div class=\"results\">" + "".join(rows) + "</div>"

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Friendly Parakeet</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 2rem;
      background-color: #f5f5f5;
    }}
    h1 {{
      margin-top: 0;
    }}
    form {{
      background: #ffffff;
      padding: 1.5rem;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
      margin-bottom: 2rem;
    }}
    label {{
      display: block;
      margin-top: 1rem;
      font-weight: bold;
    }}
    input[type=\"text\"],
    input[type=\"number\"],
    input[type=\"file\"],
    textarea {{
      width: 100%;
      padding: 0.5rem;
      margin-top: 0.5rem;
      border: 1px solid #cccccc;
      border-radius: 4px;
      box-sizing: border-box;
    }}
    textarea {{
      min-height: 120px;
    }}
    button {{
      margin-top: 1.5rem;
      padding: 0.75rem 1.5rem;
      background-color: #2563eb;
      border: none;
      border-radius: 4px;
      color: #ffffff;
      cursor: pointer;
      font-size: 1rem;
    }}
    button:hover {{
      background-color: #1d4ed8;
    }}
    .alert.error {{
      background: #fee2e2;
      color: #b91c1c;
      border: 1px solid #fecaca;
      padding: 1rem;
      border-radius: 6px;
      margin-bottom: 1.5rem;
    }}
    .results {{
      display: grid;
      gap: 1rem;
    }}
    .card {{
      background: #ffffff;
      border-radius: 8px;
      padding: 1.25rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }}
    .card h3 {{
      margin-top: 0;
    }}
    details {{
      margin-top: 0.75rem;
    }}
  </style>
</head>
<body>
  <h1>Friendly Parakeet</h1>
  <p>Analysez un devis PDF avec une question et obtenez des r\u00e9ponses par projet.</p>
  <form action=\"/analyze\" method=\"post\" enctype=\"multipart/form-data\">
    <label for=\"pdf\">Fichier PDF</label>
    <input id=\"pdf\" name=\"pdf\" type=\"file\" accept=\"application/pdf\" required />

    <label for=\"question\">Question</label>
    <textarea id=\"question\" name=\"question\" required>{question_value}</textarea>

    <label for=\"section\">Section</label>
    <input id=\"section\" name=\"section\" type=\"text\" value=\"{section_value}\" placeholder=\"ex: 25\" />

    <label for=\"top_k\">Top K</label>
    <input id=\"top_k\" name=\"top_k\" type=\"number\" min=\"1\" max=\"10\" value=\"{top_k_value}\" />

    <label for=\"chunk_size\">Chunk size</label>
    <input id=\"chunk_size\" name=\"chunk_size\" type=\"number\" min=\"100\" value=\"{chunk_size_value}\" />

    <label for=\"overlap\">Overlap</label>
    <input id=\"overlap\" name=\"overlap\" type=\"number\" min=\"0\" value=\"{overlap_value}\" />

    <label for=\"model\">Model</label>
    <input id=\"model\" name=\"model\" type=\"text\" value=\"{model_value}\" />

    <button type=\"submit\">Lancer l'analyse</button>
  </form>
  {message_block}
  {results_block}
</body>
</html>
"""


def _format_answer(answer: str) -> str:
    escaped = escape(answer)
    return "<br>".join(escaped.splitlines())


app = _create_app()


def main() -> None:
    import uvicorn

    host = os.getenv("FRIENDLY_PARAKEET_HOST", "0.0.0.0")
    port = int(os.getenv("FRIENDLY_PARAKEET_PORT", "8000"))
    uvicorn.run("friendly_parakeet.web_app:app", host=host, port=port, reload=False)


if __name__ == "__main__":  # pragma: no cover - manual launch helper
    main()
