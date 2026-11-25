from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

MODEL = "qwen2.5:3b"
EMBEDDING_MODEL = "nomic-embed-text:latest"

# Evidence limits
MAX_RESULTS = 6
PLANNER_MAX_EVIDENCE = 16
WORKER_MAX_EVIDENCE = 20

# LLM retry settings
MAX_PLANNER_ATTEMPTS = 3

# fetching web page
MAX_CHARACTERS = 10_000
TIMEOUT = 30
MAX_FETCHED_PAGES_COUNT = 20

# orchestrator
MAX_RESEARCH_STEPS = 2
MAX_FETCHES = 4

# evaluator
MAX_WEB_SEARCH_COUNT = 2

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ASSETS_DIR = PROJECT_ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

CHROMA_DIR = ASSETS_DIR / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# critique
CRITIQUE_PASS_SCORE = 6
MAX_REVISIONS = 2

# sqlite DB
CHECKPOINT_DB_PATH = Path("checkpoints.sqlite")