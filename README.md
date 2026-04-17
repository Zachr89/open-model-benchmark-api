# open-model-benchmark-api

**Benchmark open-weight models against proprietary AI—get accuracy, cost, and latency scores to pick the right model for your agent.**

## What is this?

A production-ready REST API that runs real-world coding tasks against multiple AI models (Qwen, Llama, Mistral, DeepSeek, Claude, GPT-4) and returns comparative performance reports. Submit test cases via REST endpoint or GitHub Action, receive JSON reports with accuracy percentages, token costs, latency, and confidence scores. Built for indie developers and teams selecting models for agent/tool projects.

## Features

- **Multi-model benchmarking** – Test against 5+ models in parallel (open-weight + proprietary via OpenRouter)
- **Real-world task evaluation** – Code generation, API integration, CLI tools, web scraping tasks
- **Cost-aware scoring** – Accuracy % + token cost + latency in single report
- **GitHub Action integration** – Auto-benchmark on PR merge, inline results in checks
- **Leaderboard dashboard** – Track which models win by task category
- **Freemium SaaS ready** – Free tier (10 benchmarks/mo), Pro ($29/mo, 500 benchmarks)
- **Async processing** – Celery-powered background jobs for fast API response
- **Results caching** – PostgreSQL-backed cache prevents redundant API calls
- **Webhook support** – Notify external systems when benchmarks complete

## Quick Start

### Installation

**Prerequisites:** Python 3.11+, PostgreSQL 14+, Redis 7+

1. **Clone and install dependencies:**
   ```bash
   git clone https://github.com/yourusername/open-model-benchmark-api.git
   cd open-model-benchmark-api
   pip install -e .
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenRouter API key, database URL, JWT secret
   ```

3. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

4. **Start services (Docker Compose):**
   ```bash
   docker-compose up
   ```

   API runs on `http://localhost:8000`, docs at `/docs`

### Docker

```bash
docker build -t benchmark-api .
docker run -p 8000:8000 --env-file .env benchmark-api
```

## Usage

### Benchmark a coding task

```bash
curl -X POST http://localhost:8000/v1/benchmark \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-scraper",
    "description": "Extract HN titles with BeautifulSoup",
    "code_prompt": "Write Python code that scrapes Y Combinator homepage",
    "expected_output": "Returns list of story titles",
    "task_category": "web_scraping",
    "models": ["qwen-3.6-b", "claude-opus", "gpt-4-turbo"]
  }'
```

**Response:**
```json
{
  "benchmark_id": "bench_abc123",
  "task": "web-scraper",
  "created_at": "2026-04-17T10:30:00Z",
  "results": [
    {
      "model": "qwen-3.6-b",
      "accuracy": 0.92,
      "latency_ms": 1240,
      "tokens_used": 1847,
      "cost_usd": 0.018,
      "confidence": 0.88
    },
    {
      "model": "claude-opus",
      "accuracy": 0.95,
      "latency_ms": 820,
      "tokens_used": 1620,
      "cost_usd": 0.081,
      "confidence": 0.94
    }
  ],
  "summary": "Qwen 3.6-B offers best cost/accuracy ratio (0.95x Claude at 22% cost)"
}
```

### GitHub Action integration

Add to your workflow:
```yaml
- name: Benchmark models on PR merge
  uses: yourusername/open-model-benchmark-api@v1
  with:
    task_file: .github/benchmark-tasks.json
    api_key: ${{ secrets.BENCHMARK_API_KEY }}
    models: qwen-3.6-b,claude-opus,gpt-4-turbo
```

### Leaderboard API

```bash
GET /v1/leaderboard?category=web_scraping&top=10
```

Returns models ranked by Pareto efficiency (accuracy vs. cost).

## Tech Stack

| Component | Technology |
|-----------|------------|
| **API Framework** | FastAPI (async) |
| **Task Queue** | Celery + Redis |
| **Database** | PostgreSQL + Alembic migrations |
| **Model Provider** | OpenRouter API |
| **Authentication** | JWT + API keys |
| **Payments** | Stripe (subscription) |
| **Deployment** | Docker, Docker Compose |
| **Testing** | pytest |

## Configuration

See `.env.example` for all options:
- `OPENROUTER_API_KEY` – OpenRouter credentials
- `DATABASE_URL` – PostgreSQL connection string
- `REDIS_URL` – Redis for Celery
- `JWT_SECRET` – API authentication
- `STRIPE_SECRET_KEY` – Payment processing (optional)

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/v1/benchmark` | Submit benchmark task |
| GET | `/v1/benchmark/{id}` | Get benchmark results |
| GET | `/v1/leaderboard` | View model rankings |
| POST | `/v1/auth/signup` | Create account |
| GET | `/v1/webhooks` | Manage result callbacks |

## Monetization

- **Free tier**: 10 benchmarks/month
- **Pro**: $29/month, 500 benchmarks
- **Team**: $99/month, unlimited benchmarks + organization features
- **Affiliate**: OpenRouter referral revenue (15% of referral spend)

See `MONETIZATION.md` for detailed pricing logic.

## Testing

```bash
pytest tests/ -v
pytest tests/test_benchmark.py --cov=app
```

## Deployment

Deploy to Vercel (landing page) + Railway/Render (API + Celery):

```bash
# Build and push image
docker build -t your-registry/benchmark-api .
docker push your-registry/benchmark-api

# Deploy with environment variables
vercel env pull
vercel deploy
```

## License

MIT

---

**Questions?** Open an issue or check [OVERVIEW.md](./OVERVIEW.md) for architecture details.