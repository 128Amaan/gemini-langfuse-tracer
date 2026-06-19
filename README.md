#  Gemini Observability with Langfuse

A lightweight Python utility that wraps Google Gemini API calls with full-stack LLM observability — automatic token usage tracking, cost calculation, latency measurement, and trace visualization — powered by [Langfuse](https://langfuse.com).

Drop it into any script or service that calls Gemini, and every request becomes a structured, searchable trace you can inspect in the Langfuse dashboard, with zero manual logging.

## Local CLI Responses

![local CLI call 1/2 response](images\CLI_response_1.png.png)
![local CLI call 2/2 response](images\CLI_response_2.png.png)

## Langfuse Trace Records

![Trace record part 1](images\trace_record_1.png.png)
![Trace record part 2](images\trace_record_2.png.png)

---

##  Features

-  **Automatic tracing** — every LLM call is captured as a Langfuse trace with input, output, and metadata
-  **Cost calculation** — per-call USD cost computed from token usage, ready to scale from free tier to paid pricing
-  **Latency tracking** — millisecond-level timing for every generation
-  **Token usage breakdown** — input, output, and total token counts pulled directly from the Gemini response
-  **Session & user grouping** — group related calls by `session_id` and `user_id` for per-user/per-conversation analytics
-  **Error capture** — failed calls are still traced, with the error message attached to the observation
-  **Flush-safe for scripts** — explicit flushing ensures traces aren't lost in short-lived processes

##  Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| LLM Provider | [Google Gemini API](https://ai.google.dev/) via `google-genai` |
| Observability | [Langfuse](https://langfuse.com) SDK v4 (OpenTelemetry-based) |
| Config | `python-dotenv` |
| Other | Standard library (`os`, `time`) |



##  Project Structure

```text
gemini-langfuse-tracer/
├── llm_with_tracing.py     # Main script: traced LLM call wrapper + demo runner
├── .env                    # API keys and Langfuse config (not committed)
└── README.md
```

##  Getting Started

### Prerequisites

- Python 3.10 or higher
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- A [Langfuse](https://cloud.langfuse.com) account (free tier available) with a project's Public/Secret keys

### Installation

```bash
# Clone the repository
git clone https://github.com/128Amaan/gemini-langfuse-tracer.git
cd gemini-langfuse-tracer

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

`requirements.txt`:

```text
google-genai
langfuse
python-dotenv
```

### Configuration

Create a `.env` file in the project root:

```env
# Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx
LANGFUSE_HOST=https://cloud.langfuse.com   # or your self-hosted URL
```

### Running the Project

```bash
python llm_with_tracing.py
```

This runs the built-in demo: two sample coding questions are sent to Gemini, each fully traced, with a summary (tokens, cost, latency, trace link) printed to the console.

##  Usage

Import and call `call_llm_with_tracing()` from your own code to get a traced Gemini response:

```python
from llm_with_tracing import call_llm_with_tracing

response = call_llm_with_tracing(
    user_message="Explain the difference between a stack and a queue.",
    session_id="onboarding-chat-001",
    user_id="user_42"
)

print(response)
```

Every call automatically:
1. Opens a trace (and a nested generation observation) in Langfuse
2. Sends the prompt to Gemini with the configured system prompt
3. Captures tokens, cost, and latency on success — or the error on failure
4. Flushes the trace so it's visible in the dashboard immediately

##  Deployment

This script has no server component, so "deployment" means integrating it into whatever runs your application:

- **Standalone script / cron job** — run as-is; ensure `langfuse_client.flush()` (already included) executes before the process exits.
- **Inside a long-running service** (FastAPI, worker, etc.) — Langfuse batches and flushes automatically in the background; manual `flush()` calls become optional but harmless.


##  Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please keep changes focused and include a brief description of what was changed and why.

## Author

**Amaan**
GitHub: [@128Amaan](https://github.com/128Amaan)

