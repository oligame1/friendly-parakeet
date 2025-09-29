"""Command line entry point for the Friendly Parakeet agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from .agent import Agent
from .gemini_client import GeminiClient

console = Console()


def _format_sources(sources: List[Dict[str, Any]]) -> str:
    formatted = []
    for src in sources:
        page = src.get("page_number", "?")
        score = src.get("score", 0.0)
        formatted.append(f"Page {page} (score {score:.2f})")
    return ", ".join(formatted)


def run_cli(args: argparse.Namespace) -> None:
    gemini = GeminiClient(model=args.model)
    agent = Agent.from_pdf(
        args.pdf,
        section=args.section,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        gemini=gemini,
    )

    answers = agent.answer(args.question, top_k=args.top_k)

    if args.json:
        serialisable = [
            {
                "project": answer.project,
                "answer": answer.answer,
                "confidence": answer.confidence,
                "sources": [
                    {
                        "page_number": src.page_number,
                        "score": src.score,
                        "excerpt": src.excerpt,
                    }
                    for src in answer.sources
                ],
            }
            for answer in answers
        ]
        console.print_json(json.dumps(serialisable, ensure_ascii=False, indent=2))
        return

    table = Table(title="Synthèse par projet")
    table.add_column("Projet", justify="left")
    table.add_column("Réponse", justify="left", max_width=80)
    table.add_column("Confiance", justify="center")
    table.add_column("Sources", justify="left")

    for answer in answers:
        table.add_row(
            answer.project,
            answer.answer,
            f"{answer.confidence:.2f}",
            _format_sources([
                {"page_number": src.page_number, "score": src.score} for src in answer.sources
            ]),
        )

    console.print(table)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Agent Gemini pour analyser un devis PDF.")
    parser.add_argument("--pdf", required=True, type=Path, help="Chemin vers le devis en PDF")
    parser.add_argument("--question", required=True, help="Question à poser à l'agent")
    parser.add_argument("--section", help="Numéro de section à filtrer (ex: 25)")
    parser.add_argument("--top-k", type=int, default=4, help="Nombre de passages à injecter dans Gemini")
    parser.add_argument("--chunk-size", type=int, default=1100, help="Taille des chunks en caractères")
    parser.add_argument("--overlap", type=int, default=200, help="Chevauchement entre les chunks")
    parser.add_argument("--model", default="models/gemini-pro", help="Modèle Gemini à utiliser")
    parser.add_argument("--json", action="store_true", help="Afficher les résultats au format JSON")

    args = parser.parse_args(argv)
    if not args.pdf.exists():
        raise FileNotFoundError(args.pdf)

    run_cli(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
