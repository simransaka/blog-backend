from dotenv import load_dotenv

load_dotenv()

MODEL = "qwen2.5:7b"

# Evidence limits
MAX_RESULTS = 6
PLANNER_MAX_EVIDENCE = 16
WORKER_MAX_EVIDENCE = 20

# LLM retry settings
MAX_PLANNER_ATTEMPTS = 3