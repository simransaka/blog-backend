from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

MODEL = "qwen2.5:7b"

# Evidence limits
MAX_RESULTS = 6
PLANNER_MAX_EVIDENCE = 16
WORKER_MAX_EVIDENCE = 20

# LLM retry settings
MAX_PLANNER_ATTEMPTS = 3

# fetching web page
MAX_CHARACTERS = 10_000
TIMEOUT = 30

# orchestrator
MAX_RESEARCH_STEPS = 2
MAX_FETCHES = 4

# evaluator
MAX_WEB_SEARCH_COUNT = 2

# assets directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# critique
CRITIQUE_PASS_SCORE = 7
MAX_REVISIONS = 2