# AI Engineer Course

Hands-on notebooks for learning LangChain and the OpenAI API — from first API calls through RAG.

Work through the numbered notebooks in order under `LangChain/`.

## Prerequisites

- [Python 3.13](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) (installs dependencies and manages the virtual environment)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A notebook editor: [VS Code](https://code.visualstudio.com/) / [Cursor](https://cursor.com/) with the Jupyter extension, or JupyterLab

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd AIEngineerCourse
```

### 2. Install dependencies

From the repo root:

```bash
uv sync
```

This creates a `.venv` and installs everything listed in `pyproject.toml`.

### 3. Add your API key

Create a `.env` file in the **repo root** (same folder as this README):

```env
OPENAI_API_KEY=sk-your-key-here
```

Notebooks load this automatically with `load_dotenv()`. Never commit `.env` — it is already in `.gitignore`.

### 4. Open and run notebooks

1. Open the project in VS Code or Cursor.
2. Open any notebook under `LangChain/` (start with `TheOpenAIAPI/213_FirstSteps.ipynb`).
3. Select the kernel: **Python environments → `.venv`** (the one created by `uv sync`).
4. Run cells top to bottom.

If the `.venv` kernel is missing, register it once:

```bash
uv run python -m ipykernel install --user --name=aiengineercourse --display-name="AI Engineer Course"
```

Then pick **AI Engineer Course** as the kernel.

## Course outline

| Folder | Topics |
| --- | --- |
| `LangChain/TheOpenAIAPI` | OpenAI client, message roles, inference settings |
| `LangChain/ModelInputs` | LiteLLM, messages, prompt templates |
| `LangChain/StructuredOutputs` | Pydantic schemas and custom taxonomies |
| `LangChain/LangChainExpressionLanguage` | Chains, streaming, batching, runnables |
| `LangChain/RetrievalAugmentedGeneration` | Loading, chunking, embeddings, Chroma, retrieval, generation |

Notebooks are numbered (e.g. `213_…`, `214_…`) — follow that order.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `OPENAI_API_KEY` is missing / auth errors | Confirm `.env` is in the repo root and the key is correct, then restart the kernel |
| Wrong Python / missing packages | Run `uv sync` again and select the `.venv` kernel |
| Import errors in a notebook | Kernel is not the project `.venv` — switch kernels and re-run |

## Notes

- Python **3.13+** is required (`requires-python` in `pyproject.toml`).
- RAG notebooks use local Chroma storage and OpenAI embeddings (`text-embedding-3-small`).
- Running notebooks calls the OpenAI API and may incur cost — start with the smaller models already set in the cells (`gpt-5.4-nano` / `gpt-5.4-mini`).
