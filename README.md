# Blog Backend

An AI-powered blog generation application built with **Python, LangGraph, Ollama, and Tavily**. Given a topic, the system researches relevant information when needed, creates a structured blog plan, pauses for human review and approval, generates sections using parallel workers, validates citations, critiques the draft, and saves the final result as a Markdown (`.md`) file.

## Key Features

- **Conditional research:** Determines whether a topic requires web research or can be handled using existing model knowledge.
- **Agentic research loop:** Uses web search, page fetching, evidence submission, and evaluation to gather relevant information.
- **Structured planning:** Creates a structured blog plan with sections, goals, bullet points, word counts, tags, and constraints.
- **Human-in-the-Loop (HITL):** Pauses after planning to let a human approve, reject, or edit the plan before content generation begins.
- **Plan editing:** Allows the human reviewer to modify the generated plan before dispatching tasks to workers.
- **Parallel section generation:** Uses LangGraph fan-out to generate multiple blog sections concurrently.
- **Citation fact-checking:** Validates cited URLs and checks whether available evidence supports the associated claims.
- **Iterative critique and revision:** Identifies specific sections that need corrections and sends their task IDs back to the workers.
- **Conditional workflow:** Stops revision when the critique score meets the configured threshold or the maximum number of attempts is reached.
- **Markdown output:** Combines the approved sections into a final blog document.

## Architecture Overview

The project is organized into four phases that progressively improve research quality, content reliability, and workflow control.

### Phase 1: Research Agent with Tools

Replaces one-shot research with an iterative, tool-using research agent built with LangGraph and Ollama.

- **Conditional routing:** The router determines whether research is needed and selects the workflow mode (`closed_book`, `hybrid`, or `open_book`).
- **ReAct-style research:** The agent alternates between LLM reasoning and tool execution, refining its search strategy based on retrieved information.
- **Web search:** Uses Tavily to discover relevant sources and gather initial evidence.
- **Page fetching:** Retrieves and cleans web page content so the agent can inspect information beyond search-result snippets.
- **Evidence submission:** Validates the collected evidence against the expected schema before passing it to the planning workflow.
- **Resource limits:** Enforces configurable limits on research steps and page fetches to prevent unbounded research loops.

The agent decides what to search for next rather than relying on a fixed list of queries generated upfront.

### Phase 2: Critic and Reflection Loop

Improves generated content through structured evaluation and targeted revision.

- **Parallel generation:** Uses LangGraph fan-out to distribute planned tasks among workers that generate individual blog sections concurrently.
- **Draft assembly:** Combines generated sections into a complete Markdown draft.
- **Structured critique:** Evaluates the draft against the original plan and available evidence, producing a score, sections requiring revision, and unsupported claims.
- **Targeted revision:** Uses LangGraph `Send` to rerun only the workers responsible for flagged sections, passing the critic's feedback into their prompts.
- **Section replacement:** Ensures revised sections replace their previous versions instead of creating duplicates.
- **Bounded iterations:** Uses a configurable passing score and maximum revision count to guarantee that the reflection loop terminates.
- **Final output:** Writes the final approved draft to disk only after the revision process finishes.

This phase helps improve completeness, relevance, consistency, and adherence to the original plan without regenerating every section unnecessarily.

### Phase 3: Citation Fact-Checker

Validates citations and checks whether generated claims are supported by collected evidence before critique.

- **URL validation:** Checks that each cited source URL exists in the collected evidence and removes hallucinated citations.
- **Claim verification:** Uses an LLM to determine whether the available snippet or fetched page content supports the associated claim.
- **Unsupported content handling:** Rewrites unsupported claims to `Not found in provided sources.` or removes them according to the validation rules.
- **Validation reporting:** Records the number of citations checked, removed, and rewritten, and logs the results.
- **Critic integration:** Passes the fact-checked draft to the critic for further evaluation and possible revision.

This phase reduces fabricated citations and unsupported factual claims. Its effectiveness depends on the quality and relevance of the collected evidence.

### Phase 4: Human-in-the-Loop and Checkpointing

Introduces human oversight and resumable execution using LangGraph interrupts and checkpointing.

- **Plan review:** After the planner generates the blog outline, `interrupt()` pauses execution and presents the plan in the command-line interface.
- **Approval:** Accepts the plan and continues to parallel section generation.
- **Editing:** Allows the user to modify section titles and bullet points before generation.
- **Rejection and feedback:** Sends the workflow back to the planner with the user's feedback so a revised plan can be generated.
- **Checkpoint persistence:** Uses a checkpointer and thread IDs to save workflow state and resume interrupted runs.
- **Resume support:** Supports resuming a saved workflow using a command such as `python -m src.app.main --resume <thread_id>`.
- **Automatic execution:** Provides an `--auto` option to bypass manual approval for unattended runs.

Human review provides control over the outline before the application spends resources generating the complete blog, while checkpointing enables interrupted workflows to continue from saved state.

## End-to-End Workflow

1. The router decides whether research is required.
2. The research agent gathers evidence using web search and page-fetching tools when necessary.
3. The planner generates a structured outline.
4. The human reviewer approves, edits, or rejects the outline, unless automatic mode is enabled.
5. Parallel workers generate the blog sections.
6. The citation fact-checker validates URLs and checks claims against available evidence.
7. The critic evaluates the draft and identifies sections requiring revision.
8. Flagged sections are regenerated and replace their previous versions.
9. The loop terminates when the draft passes the configured threshold or reaches the revision limit.
10. The final draft is assembled and saved as a Markdown file.

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

### Human Review During Execution

After the planner creates the blog plan, the application pauses and displays the plan for review.

Choose one of the available options:

```text
---HUMAN REVIEW REQUIRED---

Choose approve, reject, or edit - approve
```

- Enter `approve` to accept the plan and start section generation.
- Enter `reject` to return to the planner and generate a new plan.
- Enter `edit` to modify the plan before generation.

Follow the prompts displayed by the application for the selected action.

**Important:** Use `python -m src.app.main` rather than `python src/app/main.py`, because the project's package imports rely on module execution.

## 7. Find the Generated Blog

After the workflow completes, the final blog is saved as a Markdown (`.md`) file in the configured output directory.

Open the generated file to read the blog, including its structured sections and validated citations.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| LangGraph | Workflow orchestration, conditional routing, parallel execution, interrupts, checkpointing, and revision loops |
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

**Human review does not resume**

- Ensure the graph is compiled with a checkpointer.
- Use the same `thread_id` when resuming the interrupted workflow.
- Resume using `Command(resume=decision)` with a value matching what the human-review node expects.
- Confirm that the human-review node calls LangGraph's `interrupt()` function.

**Research or citation validation issues**

- Verify your Tavily API key and internet connectivity.
- Check the research limits and citation validation logic.
- Remember that a URL being accessible does not guarantee that it supports the associated claim.

**Excessive revision loops**

- Review the configured critique score threshold and maximum revision attempts.
- Ensure the critic identifies concrete defects and returns only the task IDs that genuinely require correction.

## Project Goal

This project demonstrates an agentic content-generation pipeline in which research, planning, human approval, parallel generation, citation verification, critique, and targeted revision work together to produce a structured, evidence-aware blog.

It serves as a proof of concept for building more reliable multi-agent workflows with LangGraph, local language models, and human oversight.