# open-model-benchmark-api

**Benchmark open-weight models against proprietary AI—fast, cheap, and via REST API or GitHub Action.**

## What is this?

A production-ready REST API that compares open-weight models (Qwen, Llama, Mistral, DeepSeek) against proprietary ones (Claude, GPT-4) on real-world coding tasks. Submit test cases, get comparative JSON reports with accuracy, cost, and latency scores. Built for indie developers choosing models for agent and tool projects—think Lighthouse CI but for AI model selection.

## Features

- **Unified benchmarking API** – Submit code tasks and expected outputs; get accuracy, token cost, and latency metrics across 5+ models
- **Model pool via OpenRouter** – Access Qwen, Claude, GPT-4, Llama 3.3, DeepSeek-Coder without managing multiple API keys
- **GitHub Action integration** – Auto-benchmark on PR merge for continuous model performance tracking
- **Async task processing** – Celery-backed benchmarks that run in parallel without blocking
- **Leaderboard dashboard** – See which models win on specific task categories (web scraping, API calls, CLI tools)
- **Freemium pricing** – 10 benchmarks/month free; $29/mo Pro tier (500 benchmarks)
- **Results caching** – PostgreSQL-backed cache prevents duplicate benchmark runs

## Quick Start

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone https://github.com/yourusername/open-model-benchmark-api.git
   cd open-model-benchmark-api
   pip install -e .
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Add your OpenRouter API key and database URL
   ```

3. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

The API will be available at `http://localhost:8000`.

### GitHub Action

Add to your workflow:
```yaml
- uses: yourusername/open-model-benchmark-api@v1
  with:
    test-file: './benchmarks/test_cases.json'
    models: 'qwen-7b,claude-opus,gpt-4'
```

## Usage

### REST API Example

```bash
curl -X POST http://localhost:8000/api/benchmark \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write a Python function that fetches data from an API and caches it",
    "expected_output": "def fetch_and_cache(url): ...",
    "models": ["qwen-7b", "claude-opus", "gpt-4"],
    "category": "api-calls"
  }'
```

**Response:**
```json
{
  "benchmark_id": "bm_1234567890",
  "results": [
    {
      "model": "qwen-7b",
      "accuracy": 0.85,
      "tokens_used": 240,
      "cost_usd": 0.0012,
      "latency_ms": 1240,
      "confidence": 0.92
    },
    {
      "model": "claude-opus",
      "accuracy": 0.98,
      "tokens_used": 180,
      "cost_usd": 0.0090,
      "latency_ms": 890,
      "confidence": 0.99
    }
  ],
  "timestamp": "2026-04-17T10:30:00Z"
}
```

### Python Client

```python
from open_model_benchmark import BenchmarkClient

client = BenchmarkClient(api_key="sk_...")
result = client.benchmark(
    task="Parse and validate JSON schema",
    expected_output='{"valid": true}',
    models=["qwen-7b", "claude-opus", "gpt-4"]
)
print(result.leaderboard())
```

## Tech Stack

- **Backend:** FastAPI, Uvicorn
- **Task Queue:** Celery + Redis
- **Database:** PostgreSQL + SQLAlchemy
- **Migrations:** Alembic
- **Model Access:** OpenRouter API
- **Deployment:** Docker, Docker Compose
- **Testing:** pytest
- **CI/CD:** GitHub Actions

## API Endpoints

- `POST /api/benchmark` – Submit a benchmark task
- `GET /api/benchmark/{benchmark_id}` – Get results
- `GET /api/leaderboard` – View model performance rankings
- `POST /api/auth/login` – Authenticate
- `GET /api/usage` – Check API quota

## Pricing

- **Free:** 10 benchmarks/month, public leaderboard access
- **Pro:** $29/month, 500 benchmarks/month, private results
- **Team:** $99/month, unlimited benchmarks, API access, support

## Contributing

Issues and PRs welcome. Please ensure tests pass:
```bash
pytest tests/
```

## License

MIT