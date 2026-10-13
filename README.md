# Blog Backend

An AI-powered blog generation application built with Python, LangGraph, Ollama, and Tavily. Provide a topic, and the workflow generates a structured blog post and saves it as a Markdown file.

## Prerequisites

Install the following before running the project:

- Python (a version compatible with the project's dependencies)
- [Ollama](https://ollama.com/download)
- A [Tavily API key](https://app.tavily.com/) for web research

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd blog-backend
```

## 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv myenv
.\myenv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, use Command Prompt and run:

```cmd
myenv\Scripts\activate.bat
```

## 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## 4. Download the Ollama model

Ensure Ollama is installed and running, then download the model:

```bash
ollama pull qwen2.5:7b
```

Verify that the model is available:

```bash
ollama list
```

## 5. Configure environment variables

Create your local `.env` file from the example.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder with your Tavily API key:

```dotenv
TAVILY_API_KEY=your_actual_tavily_api_key
```

Keep `.env` private. Never commit your actual API key to Git.

## 6. Run the application

From the project root directory, run:

```bash
python -m src.app.main "New discoveries in science"
```

Replace the topic with the subject you want to write about. Keep topics containing spaces inside quotation marks.

For example:

```bash
python -m src.app.main "How Retrieval-Augmented Generation works"
```

**Important:** Run the application as a Python module from the project root. Do not use `python src/app/main.py`, because the project's package imports rely on module execution.

## 7. Find the generated blog

After the workflow completes, the generated Markdown blog is saved in the project's configured output directory. Open the `.md` file to view the generated content.

## Troubleshooting

- **Ollama connection error:** Make sure Ollama is running and `qwen2.5:7b` is available.
- **Tavily authentication error:** Verify that `TAVILY_API_KEY` is set correctly in `.env`.
- **Module import error:** Run the command from the project root using `python -m src.app.main`.
- **Dependency errors:** Activate the intended virtual environment and reinstall dependencies from `requirements.txt`.