# Blog Backend

This project is an AI-powered blog generation application built with Python, LangGraph, Ollama, and Tavily. It generates structured blog posts from a given topic, with features developed incrementally across multiple Git branches.

The application uses a local language model through Ollama and supports web research through Tavily.

## Branch Overview

### `main` — Base Version

The main branch contains the base project and its core blog-generation workflow.

### `feature-branch` — Router and Planning

This branch introduces intelligent routing and planning.

- **Router:** Determines whether the topic requires web research or can be handled using the language model's existing knowledge.
- **Conditional workflow:** Routes the execution based on the router's decision.
- **Research evaluator:** Evaluates whether additional research is required when the research workflow is selected.
- **Planner:** Creates a structured blog plan using the topic and available information.

This feature helps avoid unnecessary web searches when the model's existing knowledge is sufficient.

### `agentic-feature-branch` — Agentic Research

This branch introduces the agentic research workflow (Phase 1).

- **Research orchestrator:** Coordinates the research process.
- **Web search:** Searches for relevant information using Tavily.
- **Page fetching:** Retrieves web pages for further analysis.
- **Observation loop:** Uses tool results to decide the next research action.
- **Evidence submission:** Collects and submits relevant evidence for evaluation.
- **Research evaluation:** Checks whether the gathered evidence is sufficient before proceeding to planning.

The orchestrator can perform multiple research steps until sufficient evidence is collected or a configured limit is reached.

### `critique-feature-branch` — Parallel Generation and Critique

This branch introduces parallel blog generation and iterative critique (Phase 2).

- **Fan-out:** Distributes the planned tasks to multiple workers.
- **Parallel workers:** Generate individual blog sections concurrently.
- **Critique:** Evaluates the generated content against the plan, factual correctness, completeness, and consistency.
- **Targeted revision:** Identifies specific task IDs that need corrections and sends them back for regeneration.
- **Conditional completion:** Proceeds to the reducer when the configured critique score is achieved or the maximum revision attempts are reached.
- **Reducer:** Combines the final sections into a Markdown blog file.

This workflow improves the quality of generated blogs through focused revisions instead of regenerating every section unnecessarily.

## Technology Stack

- **Python** — Application logic
- **LangGraph** — Workflow orchestration, conditional routing, parallel execution, and revision loops
- **Ollama** — Local language model execution
- **Qwen 2.5 7B** — Configured language model
- **Tavily** — Web search and research
- **Requests and BeautifulSoup** — Web page fetching and content extraction
- **Markdown** — Generated blog output

## Prerequisites

- Python compatible with the project's dependencies
- [Ollama](https://ollama.com/download)
- [Tavily API key](https://app.tavily.com/) for web research

## Setup and Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd blog-backend
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv myenv
.\myenv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Download the Ollama model

```bash
ollama pull qwen2.5:7b
```

Verify the installation:

```bash
ollama list
```

### 5. Configure environment variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Add your Tavily API key to `.env`:

```dotenv
TAVILY_API_KEY=your_actual_tavily_api_key
```

Never commit your actual API key to Git.

## Run the Application

From the project root, execute:

```bash
python -m src.app.main "Write a blog on Diwali"
```

You can replace the topic with any subject you want to explore.

The generated blog is saved as a Markdown (`.md`) file in the configured output directory.

**Note:** Run the application using `python -m src.app.main` from the project root to ensure package imports work correctly.

## Project Goal

The project demonstrates the incremental development of an agentic blog-generation system, progressing from conditional routing and structured planning to tool-driven research, parallel content generation, and targeted critique-based revision.