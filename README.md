# CloudNativeAI

## Code in collaboration with *Cursor Agent*
Labs and experiments for cloud-native AI: calling LLMs via OpenRouter and related tooling.

**In the `devtools/` folder:**

- **lab1.py** – calls OpenRouter’s chat completions API (e.g. Mistral Devstral) with a prompt and prints the response.
- **devtools.py** – developer utilities for the project.
- **hello.py** – simple script (run via `devtools.script` or directly).

Requires Python 3, `requests`, and an `OPENROUTER_API_KEY` in your environment. Run from the `devtools/` directory (e.g. `python devtools/lab1.py` from repo root or `python lab1.py` from inside `devtools/`).
