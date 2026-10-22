# Blog Backend

An AI-powered blog generation application built with **Python, LangGraph, Ollama, and Tavily**. Given a topic, the system researches relevant information when needed, generates a structured blog using parallel workers, validates citations, critiques the draft, and saves the final result as a Markdown (`.md`) file.

## Key Features

- **Conditional research:** Determines whether a topic requires web research or can be handled using existing model knowledge.
- **Agentic research loop:** Uses web search, page fetching, evidence submission, and evaluation to gather relevant information.
- **Structured planning:** Creates a blog plan before generating individual sections.
- **Parallel section generation:** Uses LangGraph fan-out to generate multiple blog sections concurrently.
- **Citation fact-checking:** Verifies cited URLs and checks whether available evidence supports the associated claims.
- **Iterative critique and revision:** Identifies specific sections that need corrections and sends their task IDs back to the workers.
- **Conditional workflow:** Stops revision when the critique score meets the configured threshold or the maximum number of attempts is reached.
- **Markdown output:** Combines the approved sections into a final blog document.

## Architecture Overview

The workflow is organized into three phases.

### Phase 1: Research and Planning

1. **Router:** Determines the topic's research requirements and selects the appropriate workflow mode.
2. **Research evaluator:** Evaluates whether the available information is sufficient.
3. **Research orchestrator:** When research is needed, coordinates web searches, page fetching, observations, and evidence submission.
4. **Evidence evaluation:** Checks whether the gathered evidence is sufficient. The research loop continues when more information is required, subject to configured limits.
5. **Planner:** Creates a structured plan for the blog using the topic and available evidence.

The router can bypass unnecessary research when the topic does not require it.

### Phase 2: Parallel Generation, Fact-Checking, and Critique

1. **Fan-out:** Distributes the planned tasks to multiple workers.
2. **Workers:** Generate individual blog sections in parallel.
3. **Citation fact-checker:** Validates citations and checks the supporting evidence for factual claims.
4. **Critic:** Evaluates the draft against the original plan, factual correctness, evidence support, completeness, and consistency.
5. **Revision decision:** Checks the critique score and configured attempt limit.
6. **Targeted revision:** If revision is required, the critic identifies the specific task IDs that need corrections. Only those sections are sent back for regeneration.
7. **Reducer:** Combines the approved sections into the final blog after the revision process finishes.

### Phase 3: Citation Fact-Checking

The citation fact-checker performs the following checks for generated sections:

- Checks whether a cited URL exists.
- Verifies whether the cited source supports the associated claim using the available evidence.
- Removes invalid or unsupported citations according to the validation rules.
- Retains citations that pass validation and preserves the verified evidence for the subsequent critique.

This helps reduce fabricated citations and unsupported factual claims before the final blog is produced.

## Prerequisites

Install the following before running the project:

- Python compatible with the project's dependencies
- [Ollama](https://ollama.com/download)
- A [Tavily API key](https://app.tavily.com/) for web research

## 1. Clone the Repository

```bash
git clone <your-repository-url>
cd blog-backend
```

Replace `<your-repository-url>` with the repository's Git URL.

## 2. Create and Activate a Virtual Environment

**Windows PowerShell**

```powershell
python -m venv myenv
.\myenv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, use Command Prompt instead:

```cmd
myenv\Scripts\activate.bat
```

## 3. Install Dependencies

From the project root, run:

```bash
python -m pip install -r requirements.txt
```

## 4. Download the Ollama Model

Ensure Ollama is installed and running, then download the model used by the application:

```bash
ollama pull qwen2.5:7b
```

Verify that the model is available:

```bash
ollama list
```

Make sure the model name matches the configuration in your project.

## 5. Configure Environment Variables

Create your local `.env` file using the example file.

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure your Tavily API key:

```dotenv
TAVILY_API_KEY=your_actual_tavily_api_key
```

Keep `.env` private. Never commit your actual API key to Git. Ensure `.env` is included in `.gitignore` and that `.env.example` contains only placeholders.

## 6. Run the Application

Run the application from the project root using Python module execution:

```bash
python -m src.app.main "New discoveries in science"
```

You can replace the topic with any subject you want to explore.

For example:

```bash
python -m src.app.main "How Retrieval-Augmented Generation works"
```

```bash
python -m src.app.main "Recent developments in artificial intelligence"
```

**Important:** Use `python -m src.app.main` rather than `python src/app/main.py`, because the project's package imports rely on module execution.

## 7. Find the Generated Blog

After the workflow completes, the final blog is saved as a Markdown (`.md`) file in the configured output directory.

Open the generated file to read the blog, including its structured sections and validated citations.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| LangGraph | Workflow orchestration, conditional routing, parallel execution, and revision loops |
| Ollama | Runs the configured local language model |
| Qwen 2.5 7B | Blog planning, generation, and evaluation |
| Tavily | Web search for research |
| Requests and BeautifulSoup | Fetching and extracting web page content |
| Pydantic | Structured model outputs and validation |
| Markdown | Final blog document format |

## Troubleshooting

**Ollama connection error**

- Ensure Ollama is installed and running.
- Verify that `qwen2.5:7b` is available using `ollama list`.
- Check the Ollama connection settings in the project configuration.

**Tavily authentication error**

- Verify that `TAVILY_API_KEY` is configured correctly in `.env`.
- Ensure the key is valid and that the environment variables are loaded.

**Module import error**

- Run the command from the repository root.
- Use `python -m src.app.main`.

**Dependency errors**

- Activate the intended virtual environment.
- Install dependencies using `python -m pip install -r requirements.txt`.

**Research or citation validation issues**

- Verify your Tavily API key and internet connectivity.
- Check the research limits and citation validation logic.
- Remember that a URL being accessible does not guarantee that it supports the associated claim.

**Excessive revision loops**

- Review the configured critique score threshold and maximum revision attempts.
- Ensure the critic identifies concrete defects and returns only the task IDs that genuinely require correction.

## Project Goal

This project demonstrates an agentic content-generation pipeline in which research, planning, parallel generation, citation verification, critique, and targeted revision work together to produce a structured, evidence-aware blog. It serves as a proof of concept for building more reliable multi-agent workflows with LangGraph and local language models.