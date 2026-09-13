# AI Engineer Course

Hands-on notebooks for learning LangChain and the OpenAI API — from first API calls through RAG.

## Getting set up

Follow these steps once before you start the coding portions of the course.

### 1. Install Cursor

1. Download and install [Cursor](https://cursor.com/) for your OS.
2. Open Cursor and sign in if prompted.
3. Use **File → Open Folder…** and select this repo (`AIEngineerCourse`).

Cursor is a VS Code–compatible editor, so most VS Code extensions and workflows work the same way.

### 2. Install the Jupyter extension in Cursor

Notebooks in this course need the Jupyter extension:

1. Open the Extensions view (`Ctrl+Shift+X` on Windows / Linux, `Cmd+Shift+X` on macOS).
2. Search for **Jupyter** (publisher: Microsoft).
3. Install **Jupyter**. Also install **Python** (publisher: Microsoft) if it is not already installed — it helps Cursor find interpreters and kernels.
4. Reload the window if Cursor asks you to.

You should now be able to open `.ipynb` files and pick a kernel from the top-right of the notebook.

### 3. Install uv

[uv](https://docs.astral.sh/uv/) installs Python packages and manages the project virtual environment.

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After install, close and reopen your terminal (or Cursor) so `uv` is on your `PATH`. Confirm with:

```powershell
uv --version
```

**macOS / Linux:** see the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/).

### 4. Get an OpenAI API key

1. Create or sign in to an account at [platform.openai.com](https://platform.openai.com/).
2. Go to [API keys](https://platform.openai.com/api-keys).
3. Create a new secret key and copy it immediately (you will not be able to view it again).
4. Keep the key private — do not commit it or share it in chat/screenshots.

You will need a funded OpenAI account (or free trial credits). Running notebooks calls the API and may incur cost; the notebooks default to smaller models to keep usage low.

### 5. Clone the repo (if you have not already)

```bash
git clone <repo-url>
cd AIEngineerCourse
```

Or open the folder you already have in Cursor (**File → Open Folder…**).

### 6. Install project dependencies

From the repo root (in Cursor’s terminal: **Terminal → New Terminal**):

```bash
uv sync
```

This creates a `.venv` and installs everything listed in `pyproject.toml`. Python **3.13+** is required; `uv` can fetch a suitable Python if needed.

### 7. Add your API key

Create a `.env` file in the **repo root** (same folder as this README):

```env
OPENAI_API_KEY=sk-your-key-here
```

Notebooks load this automatically with `load_dotenv()`. Never commit `.env` — it is already in `.gitignore`.

### 8. Open and run notebooks

1. In Cursor, open any notebook under `LangChain/` (start with `TheOpenAIAPI/213_FirstSteps.ipynb`).
2. Select the kernel: **Python environments →** `.venv` (the one created by `uv sync`).
3. Run cells top to bottom.

If the `.venv` kernel is missing, register it once:

```bash
uv run python -m ipykernel install --user --name=aiengineercourse --display-name="AI Engineer Course"
```

Then pick **AI Engineer Course** as the kernel.

## Course outline


| Folder                                   | Topics                                                       |
| ---------------------------------------- | ------------------------------------------------------------ |
| `LangChain/TheOpenAIAPI`                 | OpenAI client, message roles, inference settings             |
| `LangChain/ModelInputs`                  | LiteLLM, messages, prompt templates                          |
| `LangChain/StructuredOutputs`            | Pydantic schemas and custom taxonomies                       |
| `LangChain/LangChainExpressionLanguage`  | Chains, streaming, batching, runnables                       |
| `LangChain/RetrievalAugmentedGeneration` | Loading, chunking, embeddings, Chroma, retrieval, generation |


Notebooks are numbered (e.g. `213_…`, `214_…`) — follow that order.

## Troubleshooting


| Problem                                   | Fix                                                                                |
| ----------------------------------------- | ---------------------------------------------------------------------------------- |
| `uv` is not recognized                    | Reopen the terminal after install; confirm with `uv --version`                     |
| Jupyter / kernel UI missing               | Install the Microsoft **Jupyter** (and **Python**) extensions, then reload         |
| `OPENAI_API_KEY` is missing / auth errors | Confirm `.env` is in the repo root and the key is correct, then restart the kernel |
| Wrong Python / missing packages           | Run `uv sync` again and select the `.venv` kernel                                  |
| Import errors in a notebook               | Kernel is not the project `.venv` — switch kernels and re-run                      |




## Notes

- Python **3.13+** is required (`requires-python` in `pyproject.toml`).
- RAG notebooks use local Chroma storage and OpenAI embeddings (`text-embedding-3-small`).
- Running notebooks calls the OpenAI API and may incur cost — start with the smaller models already set in the cells (`gpt-5.4-nano` / `gpt-5.4-mini`).

