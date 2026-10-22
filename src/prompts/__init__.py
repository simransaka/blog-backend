from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent

PLANNER_PROMPT = (PROMPTS_DIR / "planner_prompt.md").read_text(
    encoding="utf-8"
)

WORKER_PROMPT = (PROMPTS_DIR / "worker_prompt.md").read_text(
    encoding="utf-8"
)

RESEARCH_PROMPT = (PROMPTS_DIR / "research_prompt.md").read_text(
    encoding="utf-8"
)

ROUTER_PROMPT = (PROMPTS_DIR / "router_prompt.md").read_text(
    encoding="utf-8"
)

ORCHESTRATOR_PROMPT = (PROMPTS_DIR / "orchestrator_prompt.md").read_text(
    encoding="utf-8"
)

EVALUATOR_PROMPT = (PROMPTS_DIR / "evaluator_prompt.md").read_text(
    encoding="utf-8"
)

CRITIQUE_PROMPT = (PROMPTS_DIR / "critique_prompt.md").read_text(
    encoding="utf-8"
)