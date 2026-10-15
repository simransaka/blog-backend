from dotenv import load_dotenv

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
TIMEOUT = 15

# orchestrator
MAX_RESEARCH_STEPS = 8
MAX_FETCHES = 4