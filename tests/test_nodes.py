from types import SimpleNamespace
import importlib

from src.nodes import route_next
import src.nodes as reducer

tavily_module = importlib.import_module(
    "src.tools.web_search"
)

reducer_module = importlib.import_module("src.nodes.reducer")

# Test 1: Router chooses the correct next node.
def test_route_next():
    assert route_next({"needs_research": True}) == "research"
    assert route_next({"needs_research": False}) == "planner"


# Test 2: Reducer sorts sections and creates Markdown.
def test_reducer_sorts_sections_and_saves_markdown(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(reducer_module, "OUTPUT_DIR", tmp_path)

    fake_plan = SimpleNamespace(blog_title="Test Blog")

    state = {
        "plan": fake_plan,
        "sections": [
            (2, "## Second Section"),
            (1, "## First Section"),
        ],
    }

    result = reducer_module.reducer(state)

    expected = (
        "# Test Blog\n\n"
        "## First Section\n\n"
        "## Second Section"
    )

    assert result["final"] == expected

    output_file = tmp_path / "test_blog.md"
    assert output_file.read_text(encoding="utf-8") == expected


# Test 3: Tavily results are normalized correctly.
# Test 3: Tavily results are normalized correctly.
def test_tavily_result_normalization(monkeypatch):
    fake_results = [
        {
            "title": "Example Article",
            "url": "https://example.com/article",
            "content": "An article about science.",
            "published_date": "2026-09-15",
            "source": "example.com",
        }
    ]

    def fake_invoke(self, query):
        assert query == {
            "query": "science discoveries",
            "max_results": 3,
        }
        return fake_results

    monkeypatch.setattr(
        type(tavily_module.tool),
        "invoke",
        fake_invoke,
    )

    results = tavily_module.web_search(
        "science discoveries",
        max_results=3,
    )

    assert results == [
        {
            "title": "Example Article",
            "url": "https://example.com/article",
            "snippet": "An article about science.",
            "published_at": "2026-09-15",
            "source": "example.com",
        }
    ]