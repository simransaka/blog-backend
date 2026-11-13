import importlib
import json
from types import SimpleNamespace

from src.models import EvidenceItem, FetchedPageContent


orchestrator_module = importlib.import_module("src.nodes.orchestrator")
evaluator_module = importlib.import_module("src.nodes.evaluator")
fetch_page_module = importlib.import_module("src.tools.fetch_page")


def _tool_call(name, arguments):
    return SimpleNamespace(
        function=SimpleNamespace(name=name, arguments=arguments)
    )


def test_orchestrator_searches_and_fetches_page(monkeypatch):
    calls = [
        SimpleNamespace(
            message=SimpleNamespace(
                tool_calls=[
                    _tool_call("web_search", {"query": "climate adaptation"})
                ]
            )
        ),
        SimpleNamespace(
            message=SimpleNamespace(
                tool_calls=[
                    _tool_call(
                        "fetch_page",
                        {"url": "https://example.com/climate"},
                    )
                ]
            )
        ),
    ]
    chat_inputs = []
    search_arguments = []

    def fake_chat(**kwargs):
        chat_inputs.append(kwargs)
        return calls.pop(0)

    def fake_search(args):
        search_arguments.append(args)
        return [
            {
                "title": "Climate adaptation",
                "url": "https://example.com/climate",
                "snippet": "Evidence about adaptation.",
            }
        ]

    monkeypatch.setattr(orchestrator_module.ollama, "chat", fake_chat)
    monkeypatch.setattr(
        orchestrator_module,
        "TOOL_MAP",
        {
            "web_search": SimpleNamespace(invoke=fake_search),
            "fetch_page": SimpleNamespace(
                invoke=lambda args: {
                    "url": args["url"],
                    "content": "Detailed page evidence.",
                }
            ),
        },
    )
    monkeypatch.setattr(
        orchestrator_module,
        "search_result_validator",
        lambda evidence: evidence,
    )

    result = orchestrator_module.orchestrator(
        {
            "topic": "Climate adaptation",
            "mode": "open_book",
            "needs_research": True,
            "evaluator_feedback": "Find a primary source.",
            "evidence": [],
            "fetched_page_content": [],
        }
    )

    assert result["web_search_count"] == 1
    assert result["fetch_count"] == 1
    assert result["evidence"] == [
        EvidenceItem(
            title="Climate adaptation",
            url="https://example.com/climate",
            snippet="Evidence about adaptation.",
        )
    ]
    assert result["fetched_page_content"] == [
        FetchedPageContent(
            url="https://example.com/climate",
            content="Detailed page evidence.",
        )
    ]
    assert "Find a primary source." in chat_inputs[0]["messages"][1]["content"]
    assert "Detailed page evidence." in chat_inputs[1]["messages"][-1]["content"]
    assert search_arguments == [{"query": "climate adaptation"}]
    assert result["research_stalled"] is False


def test_orchestrator_stops_when_model_does_not_call_tools(monkeypatch):
    def fake_chat(**kwargs):
        assert kwargs["tools"] == orchestrator_module.TOOLS
        return SimpleNamespace(message=SimpleNamespace(tool_calls=None))

    monkeypatch.setattr(
        orchestrator_module.ollama,
        "chat",
        fake_chat,
    )

    result = orchestrator_module.orchestrator(
        {
            "topic": "Climate adaptation",
            "mode": "open_book",
            "needs_research": True,
            "evidence": [],
            "fetched_page_content": [],
        }
    )

    assert result["research_stalled"] is True
    assert result["research_steps"] == 0


def test_fetch_page_truncates_to_requested_character_limit(monkeypatch):
    class FakeResponse:
        text = "<html><body>ABCDEFGHIJKLM</body></html>"

        def raise_for_status(self):
            return None

    def fake_get(url, **kwargs):
        assert url == "https://example.com"
        assert kwargs["timeout"] > 0
        return FakeResponse()

    monkeypatch.setattr(
        fetch_page_module.requests,
        "get",
        fake_get,
    )

    result = fetch_page_module.fetch_page.invoke(
        {
            "url": "https://example.com",
            "max_characters": 5,
        }
    )

    assert result == {
        "url": "https://example.com",
        "content": "ABCDE",
    }


def test_evaluator_includes_fetched_page_content(monkeypatch):
    chat_inputs = []

    def fake_chat(**_kwargs):
        chat_inputs.append(_kwargs)
        return SimpleNamespace(
            message=SimpleNamespace(
                content=json.dumps(
                    {
                        "sufficient": True,
                        "feedback": "Evidence is adequate.",
                    }
                )
            )
        )

    monkeypatch.setattr(evaluator_module.ollama, "chat", fake_chat)

    result = evaluator_module.evaluator(
        {
            "topic": "Climate adaptation",
            "mode": "open_book",
            "evidence": [],
            "fetched_page_content": [
                FetchedPageContent(
                    url="https://example.com/climate",
                    content="Detailed page evidence.",
                )
            ],
        }
    )

    assert result == {
        "evidence_sufficient": True,
        "evaluator_feedback": "Evidence is adequate.",
    }
    assert "Detailed page evidence." in chat_inputs[0]["messages"][1]["content"]
