from friendly_parakeet.agent import Agent
from friendly_parakeet.gemini_client import GeminiClient
from friendly_parakeet.pdf_reader import Page


class MockGemini(GeminiClient):
    def __init__(self) -> None:
        super().__init__(model="mock")


def test_agent_produces_answers_per_project():
    pages = {
        "Projet A": [
            Page(number=1, text="Projet : Projet A\nSection 25 plomberie - coût 100$"),
            Page(number=2, text="Les travaux incluent l'installation des tuyaux."),
        ],
        "Projet B": [
            Page(number=3, text="Projet : Projet B\nSection 25 électricité - coût 200$"),
        ],
    }

    agent = Agent.from_pages(pages, gemini=MockGemini())
    answers = agent.answer("Quel est le coût en section 25?", top_k=1)

    assert {answer.project for answer in answers} == {"Projet A", "Projet B"}
    for answer in answers:
        assert "Section" in answer.answer or "Synthèse" in answer.answer
        assert answer.confidence >= 0
        assert answer.sources
