**Review: feature-branch**

Good work splitting the single script into models, prompts, router, retrieval and services. It's much easier to follow now. The atomic file write in the reducer is a nice touch too. Below are the things I'd like fixed, most important first.

**Bugs / must fix**

- **`tavily_search.py:23`**: the brackets are in the wrong place. `r.get("published_date" or r.get("published_at"))` always becomes `r.get("published_date")`, so the `published_at` fallback never runs. It should be `r.get("published_date") or r.get("published_at")`. This bug was already on `main`, but please fix it while you're in this file.
- **`prompts/planner.py`**: the prompt got mangled when it was moved. It's a triple-quoted string that still has the old `"..."\n"` concatenation pieces inside it, so the model sees stray quotes and big blocks of indentation. Please rewrite it as a clean triple-quoted string, the way the other prompts are.
- **The planner prompt asks for `section_type='common_mistakes'`**, but `Task` has no `section_type` field. The model can't satisfy that rule. Either add the field or remove the line.
- **The worker never sees the evidence snippets.** It only gets `title | url | date`. The prompt says "only make claims supported by evidence", but the model has nothing to check claims against, so it invents details. Look at the generated September 2026 blog: the conference dates and locations are almost certainly made up. Pass the `snippet` through as well.
- **There's no handling for bad LLM output.** Every `model_validate_json` call will throw if the 7B model returns invalid JSON or breaks a constraint (for example, 2 bullets instead of 3–5). One bad response kills the whole run. Add a small retry, say 2–3 attempts, around these calls.
- **Context size.** In `research_node`, up to 10 queries × 6 results get dumped into one prompt as a Python `repr`. That will overflow Ollama's default context window, which is small, and Ollama truncates silently. Set `options={"num_ctx": ...}` and/or cap and trim the raw results first.
- **The reducer assumes `src/outputs/` already exists.** On a fresh clone, or if the folder gets deleted, the temp file creation fails. Add `output_path.parent.mkdir(parents=True, exist_ok=True)`.

**Cleanup**

- **`planner_service.py`** still has a copy of `fanout` and an unused `Send` import. The real one now lives in `fanout_service.py`, so delete the copy.
- **`worker_service.py:20`**: `blog_title` is assigned and never used.
- **`research_node.py`** imports `_tavily_search` from its own package (`from src.retrieval import ...`). That only works because of the import order in `__init__.py`. Use `from .tavily_search import ...` instead.
- **The underscore in `_tavily_search`** marks it as private, but `__init__.py` exports it. Drop the underscore.
- **`src/__init__.py` re-exports `State` and `MODEL`.** That ties every module to the package's import order. Import from `src.config` and `src.state` directly instead.
- **Magic numbers** are scattered around: `MAX_RESULTS = 6`, `[:16]` in the planner, `[:20]` in the worker. Move them into `config.py` so they're in one place and consistent.
- **Replace the `print`s with `logging`.** Some of them are also misleading. For example, `"need to do tavily search"` prints *after* the search has already finished.
- **`TavilySearchResults`** is created again for every query. Create it once. Also, it's deprecated in `langchain_community`, so consider moving to the `langchain-tavily` package.
- **Typo** in `plan.py`: "who this blog **id** for".

**Structure / design**

- The node functions are spread across `router/`, `retrieval/` and `services/`, with `fanout` in a file of its own. A single `nodes/` package would be more predictable.
- Sections are joined in whatever order the parallel workers come back. The old code had `tuple[int, str]` in the state for this. Return `(task.id, markdown)` from the worker and sort in the reducer so the order is guaranteed.
- `mode` in `State` is a plain `str`. Use the same `Literal` as in `RouterDecision`.
- The planner prompt is written for developer and technical blogs ("Assume the reader is a developer", "MWE"), but the sample topic is general science news. Either make the prompt generic or decide it's a tech-only tool and say so.
- `main.py` hard-codes the topic. Take it as a command-line argument.

**Repo hygiene**

- **Generated blogs are committed** inside `src/outputs/`. Move the output folder out of `src/` (or make it configurable) and add it to `.gitignore`. Also, a blog with the same title will silently overwrite the old one.
- **`requirements.txt` has no version pins.** LangGraph and LangChain change a lot between versions, so pin them.
- **The README needs real setup steps:** the `ollama pull qwen2.5:7b` step, `TAVILY_API_KEY`, a `.env.example` (`.gitignore` already allows one), and how to run the project. It has to be `python -m src.app.main`; `python src/app/main.py` won't work.
- **The commit messages** ("adding files", "modified reducer_service") don't tell me *why* anything changed. Please make them more descriptive from here on.
- **There are no tests.** At minimum, add one for `route_next`, the reducer (using a fake plan and fake sections), and the Tavily result normalisation.

Fix the bugs section first, then we can go over the rest.
