# README Updates — Markdown Storage and Embeddings

## 1. Update the Project Description

Add this sentence to the end of the opening description:

The application also assigns a unique ID to each generated Markdown file, stores its metadata and file path in MySQL, and generates document embeddings using Ollama and ChromaDB to support future file-specific retrieval.

---

## 2. Add These Key Features

Add the following bullets under **Key Features**:

- **Markdown file identification:** Assigns a unique ID to every generated Markdown file.
- **MySQL metadata storage:** Stores each file's ID, title, file path, version, embedding status, and timestamps in a MySQL database.
- **Persistent document storage:** Saves generated Markdown files in the project's `outputs/` directory.
- **Markdown chunking:** Splits generated Markdown documents into smaller, overlapping chunks while preserving heading structure.
- **Embedding generation:** Uses Ollama's `nomic-embed-text` model to generate vector embeddings for Markdown chunks.
- **Vector storage:** Stores embeddings and associated metadata in a persistent ChromaDB collection for future retrieval.

---

## 3. Add a New Architecture Phase

Add this as **Phase 5**, after Phase 4.

### Phase 5: Markdown Persistence and Embeddings Generation

Introduces persistent storage for generated blogs and prepares their content for future semantic retrieval.

- **Unique file IDs:** Generates a unique identifier for each completed Markdown file.
- **Markdown file storage:** Saves the final blog document in the project's `outputs/` directory.
- **MySQL integration:** Uses SQLAlchemy and PyMySQL to connect to MySQL and manage Markdown file metadata.
- **Metadata registration:** Stores the file ID, title, file path, version, embedding status, and creation and update timestamps in the `markdown_files` table.
- **Document loading:** Reads the saved Markdown file before starting the embedding process.
- **Recursive text splitting:** Divides the Markdown content into smaller chunks using heading-aware separators.
- **Overlapping chunks:** Uses a chunk size of approximately 800 characters and an overlap of 120 characters to preserve context between consecutive chunks.
- **Embedding generation:** Uses Ollama's `nomic-embed-text` model to convert each text chunk into a numerical vector representation.
- **Vector database:** Stores the generated embeddings in a persistent ChromaDB collection named `markdown_documents`.
- **Chunk metadata:** Associates each stored chunk with its `file_id`, document title, chunk index, and version.
- **Persistent storage:** Keeps ChromaDB data in the project's `assets/chroma_db/` directory so the vector database can be reused across application runs.
- **Embedding reuse:** Checks the file ID and version to avoid unnecessarily generating embeddings again for an already indexed version of a document.

This phase separates document metadata from vector storage: MySQL manages the Markdown file records, while ChromaDB stores the vector representations of the document chunks.

---

## 4. Update the End-to-End Workflow

Replace your existing workflow with this updated version:

1. The router decides whether research is required.
2. The research agent gathers evidence using web search and page-fetching tools when necessary.
3. The planner generates a structured outline.
4. The human reviewer approves, edits, or rejects the outline, unless automatic mode is enabled.
5. Parallel workers generate the blog sections.
6. The citation fact-checker validates URLs and checks claims against available evidence.
7. The critic evaluates the draft and identifies sections requiring revision.
8. Flagged sections are regenerated and replace their previous versions.
9. The loop terminates when the draft passes the configured threshold or reaches the revision limit.
10. The final draft is assembled and saved as a Markdown file in the `outputs/` directory.
11. A unique ID is assigned to the generated Markdown file.
12. The file's metadata and path are registered in the MySQL `markdown_files` table.
13. The saved Markdown document is loaded and split into smaller, overlapping chunks.
14. Ollama's `nomic-embed-text` model generates embeddings for the chunks.
15. The embeddings and their associated metadata are stored in the persistent ChromaDB collection `markdown_documents`.

---

## 5. Add Database and Embeddings Setup

Add these steps after your existing **Configure Environment Variables** section.

### Configure MySQL

Ensure that MySQL Server is installed and running. Create a database for the application.

For example, you can create a database named `blog_backend`:

```sql
CREATE DATABASE blog_backend;
```

Configure the database connection details in your `.env` file:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_NAME=blog_backend
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
```

The application uses SQLAlchemy and PyMySQL to connect to MySQL. The database table is initialized through the application's database setup.

### Download the Embedding Model

The project uses Ollama's `nomic-embed-text` model to generate embeddings.

Run:

```bash
ollama pull nomic-embed-text
```

Verify that the model is available:

```bash
ollama list
```

Make sure Ollama is running before starting the application.

---

## 6. Add a Storage and Embeddings Section

Add this section after **Find the Generated Blog**.

### Generated Markdown Files and Embeddings

After the blog generation and revision workflow completes, the application performs the following storage operations:

**Markdown file storage**

- Saves the final Markdown document in `outputs/`.
- Assigns a unique ID to the generated file.
- Registers the file's metadata and path in MySQL.

**MySQL metadata**

The `markdown_files` table maintains the following information:

| Column | Purpose |
|---|---|
| `id` | Unique identifier for the Markdown file |
| `title` | Blog title |
| `file_path` | Path to the saved Markdown file |
| `version` | Document version |
| `embedding_status` | Tracks the embedding-generation status |
| `created_at` | Record creation timestamp |
| `updated_at` | Last update timestamp |

**Embedding generation**

- Loads the saved Markdown file.
- Splits the content into smaller chunks using recursive text splitting.
- Preserves heading structure where possible.
- Generates embeddings using `nomic-embed-text`.
- Stores the vectors in ChromaDB along with their document metadata.

**ChromaDB configuration**

| Setting | Value |
|---|---|
| Storage directory | `assets/chroma_db/` |
| Collection name | `markdown_documents` |
| Embedding model | `nomic-embed-text` |
| Chunk size | 800 characters |
| Chunk overlap | 120 characters |
| Metadata | `file_id`, `title`, `chunk_index`, `version` |

MySQL stores the document records and their file paths, while ChromaDB stores the vector embeddings of the document chunks. This provides the foundation for implementing document-specific semantic search and retrieval in a future chatbot.

---

## 7. Update the Technology Stack

Replace your existing technology stack table with this updated version:

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| LangGraph | Workflow orchestration, conditional routing, parallel execution, interrupts, checkpointing, and revision loops |
| Ollama | Runs local language and embedding models |
| Qwen2.5 3B | Configured language model for blog planning, generation, and evaluation |
| Nomic Embed Text Latest | Generates vector embeddings for Markdown chunks |
| Tavily | Web search for research |
| Requests and BeautifulSoup | Fetching and extracting web page content |
| Pydantic | Structured model outputs and validation |
| SQLAlchemy | Database ORM and MySQL integration |
| PyMySQL | MySQL database driver |
| MySQL | Stores Markdown file metadata and file paths |
| ChromaDB | Persistent vector database for document embeddings |
| Markdown | Final blog document format |

---

## 8. Update the Project Goal

Replace your existing Project Goal section with:

## Project Goal

This project demonstrates an agentic content-generation pipeline in which research, planning, human approval, parallel generation, citation verification, critique, and targeted revision work together to produce structured, evidence-aware blogs.

It also implements persistent document storage and embedding generation. Each generated Markdown file receives a unique identifier, its metadata is stored in MySQL, and its content is converted into vector embeddings using Ollama and stored in ChromaDB.

The project serves as a proof of concept for building more reliable multi-agent workflows with LangGraph, local language models, human oversight, relational databases, and vector databases. The stored document embeddings provide the foundation for future semantic retrieval and document-specific chatbot functionality.