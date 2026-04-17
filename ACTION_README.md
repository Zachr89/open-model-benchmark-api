# Open Model Benchmark - GitHub Action

**Benchmark AI models (Qwen, Llama, Claude, GPT-4) on coding tasks directly in your CI/CD pipeline.**

Like Lighthouse CI for performance testing, but for evaluating AI model accuracy, cost, and latency on real-world code generation tasks.

## What does this do?

This GitHub Action runs your code generation prompts against multiple AI models (open-weight and proprietary) and returns comparative performance metrics:

- **Accuracy** - How well each model solved the task (0-100%)
- **Cost** - Token usage and USD cost per request
- **Latency** - Response time in milliseconds
- **Confidence** - Model's self-assessed certainty

Perfect for:
- Validating which AI model works best for your use case before committing
- Tracking model performance regressions over time
- Comparing open-source vs. proprietary model trade-offs
- Making data-driven decisions about LLM selection

## Quick Start

### 1. Get an API Key

Sign up for a free account at [benchmark-api.com/signup](https://benchmark-api.com/signup) (10 benchmarks/month free).

Add your API key to repository secrets:
- Go to your repo **Settings → Secrets and variables → Actions**
- Create new secret: `BENCHMARK_API_KEY`

### 2. Add to Your Workflow

Create `.github/workflows/benchmark.yml`:

```yaml
name: AI Model Benchmark

on:
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - name: Benchmark code generation
        uses: yourusername/open-model-benchmark-api@v1
        with:
          api_key: ${{ secrets.BENCHMARK_API_KEY }}
          task_name: 'web-scraper'
          task_description: 'Extract article titles from news site'
          code_prompt: 'Write Python code using BeautifulSoup to scrape Hacker News homepage and return list of story titles'
          expected_output: 'Returns array of strings (titles)'
          models: 'qwen-3.6-b,claude-opus,gpt-4-turbo'
          task_category: 'web_scraping'
```

### 3. Run and View Results

Push a PR or trigger manually. The action will:
1. Submit benchmark to API
2. Wait for results (30-60 seconds)
3. Output comparison table
4. Upload detailed JSON results as artifact

## Usage Examples

### Basic Usage - Single Benchmark

```yaml
- name: Benchmark API client generation
  uses: yourusername/open-model-benchmark-api@v1
  with:
    api_key: ${{ secrets.BENCHMARK_API_KEY }}
    task_name: 'stripe-api-client'
    code_prompt: 'Generate TypeScript code to create a Stripe customer and save payment method'
    expected_output: 'Returns customer ID and payment method ID'
    models: 'qwen-3.6-b,gpt-4-turbo'
```

### Comment Results on PR

Automatically post benchmark results as PR comment:

```yaml
- name: Benchmark with PR comment
  uses: yourusername/open-model-benchmark-api@v1
  with:
    api_key: ${{ secrets.BENCHMARK_API_KEY }}
    task_name: 'data-processing'
    code_prompt: 'Parse CSV with pandas and calculate monthly revenue'
    expected_output: 'Returns dict with month:revenue pairs'
    comment_on_pr: 'true'
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Result:** Creates a formatted comment like this:

```markdown
## 🤖 AI Model Benchmark Results

**Task:** data-processing

| Model | Accuracy | Latency | Cost | Tokens | Confidence |
|-------|----------|---------|------|--------|------------|
| qwen-3.6-b | 92.0% | 1240ms | $0.0180 | 1847 | 88% |
| claude-opus | 95.0% | 820ms | $0.0810 | 1620 | 94% |
| gpt-4-turbo | 93.5% | 950ms | $0.0520 | 1580 | 91% |

**Summary:** Qwen 3.6-B offers best cost/accuracy ratio (0.95x Claude at 22% cost)

📊 [View full results](https://api.openbenchmark.dev/v1/benchmark/bench_abc123)

*Benchmark ID: bench_abc123*
```

### Fail Build on Low Accuracy

Prevent merging if model performance drops below threshold:

```yaml
- name: Benchmark with quality gate
  uses: yourusername/open-model-benchmark-api@v1
  with:
    api_key: ${{ secrets.BENCHMARK_API_KEY }}
    task_name: 'sql-query-gen'
    code_prompt: 'Generate SQL to find top 10 customers by revenue in 2024'
    expected_output: 'Returns valid SELECT query with JOIN and GROUP BY'
    fail_on_low_score: '0.85'  # Fail if best model < 85% accuracy
```

### Multiple Benchmarks in One Workflow

Test different model categories:

```yaml
jobs:
  benchmark-code:
    runs-on: ubuntu-latest
    steps:
      - name: Test small models
        uses: yourusername/open-model-benchmark-api@v1
        with:
          api_key: ${{ secrets.BENCHMARK_API_KEY }}
          task_name: 'simple-function'
          code_prompt: 'Write function to validate email addresses'
          expected_output: 'Returns boolean'
          models: 'qwen-3.6-b,llama-3.3-8b'
      
      - name: Test large models
        uses: yourusername/open-model-benchmark-api@v1
        with:
          api_key: ${{ secrets.BENCHMARK_API_KEY }}
          task_name: 'complex-refactor'
          code_prompt: 'Refactor this class to use dependency injection'
          expected_output: 'Modified code with constructor injection'
          models: 'claude-opus,gpt-4-turbo'
```

### Use Benchmark Results in Subsequent Steps

```yaml
- name: Run benchmark
  id: bench
  uses: yourusername/open-model-benchmark-api@v1
  with:
    api_key: ${{ secrets.BENCHMARK_API_KEY }}
    task_name: 'test-task'
    code_prompt: 'Generate unit tests for authentication'
    expected_output: 'Jest test suite'

- name: Display winner
  run: |
    echo "Best model: ${{ steps.bench.outputs.best_model }}"
    echo "Accuracy: ${{ steps.bench.outputs.best_accuracy }}"
    echo "Cost: ${{ steps.bench.outputs.best_cost }}"
    echo "View results: ${{ steps.bench.outputs.results_url }}"

- name: Save to file
  run: echo '${{ steps.bench.outputs.results_json }}' > results.json
```

### Schedule Regular Benchmarks

Track model performance over time:

```yaml
name: Weekly Model Benchmark

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9am UTC
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - name: Benchmark weekly task
        uses: yourusername/open-model-benchmark-api@v1
        with:
          api_key: ${{ secrets.BENCHMARK_API_KEY }}
          task_name: 'weekly-baseline'
          code_prompt: 'Standard coding task for tracking'
          expected_output: 'Expected behavior'
          upload_results: 'true'
      
      - name: Compare with previous week
        run: |
          # Download last week's artifact and compare
          # (custom logic here)
```

### Custom API Endpoint

Use self-hosted instance:

```yaml
- uses: yourusername/open-model-benchmark-api@v1
  with:
    api_key: ${{ secrets.BENCHMARK_API_KEY }}
    api_endpoint: 'https://benchmark.yourcompany.com'
    task_name: 'internal-task'
    code_prompt: 'Your prompt'
    expected_output: 'Expected output'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `api_key` | API key from benchmark-api.com | ✅ Yes | - |
| `task_name` | Name for this benchmark | ✅ Yes | - |
| `task_description` | What the code should do | ❌ No | - |
| `code_prompt` | Prompt for AI models | ✅ Yes | - |
| `expected_output` | Expected behavior description | ✅ Yes | - |
| `models` | Comma-separated model list | ❌ No | `qwen-3.6-b,claude-opus,gpt-4-turbo` |
| `task_category` | Task category (see below) | ❌ No | `code_generation` |
| `api_endpoint` | API base URL | ❌ No | `https://api.openbenchmark.dev` |
| `fail_on_low_score` | Fail if accuracy < threshold (0.0-1.0) | ❌ No | `0.0` |
| `comment_on_pr` | Post results as PR comment | ❌ No | `false` |
| `upload_results` | Upload results artifact | ❌ No | `true` |

### Task Categories

- `code_generation` - General code writing
- `web_scraping` - Data extraction tasks
- `api_integration` - API client code
- `cli_tools` - Command-line utilities
- `data_processing` - Data transformation

### Available Models

- `qwen-3.6-b` - Qwen 3.6B (cost-effective)
- `qwen-3.6-14b` - Qwen 14B (balanced)
- `qwen-3.6-35b` - Qwen 35B (high-performance)
- `llama-3.3-8b` - Meta Llama 3.3 8B
- `llama-3.3-70b` - Meta Llama 3.3 70B
- `claude-opus` - Anthropic Claude Opus
- `claude-sonnet` - Anthropic Claude Sonnet
- `gpt-4-turbo` - OpenAI GPT-4 Turbo
- `gpt-4o` - OpenAI GPT-4o
- `deepseek-coder` - DeepSeek Coder

Full list: [benchmark-api.com/models](https://benchmark-api.com/models)

## Outputs

| Output | Description |
|--------|-------------|
| `benchmark_id` | Unique ID for this run |
| `best_model` | Name of highest-accuracy model |
| `best_accuracy` | Accuracy of best model (0.0-1.0) |
| `best_cost` | Cost in USD of best model |
| `results_url` | URL to view full results |
| `results_json` | Complete JSON response |

## Artifacts

When `upload_results: 'true'`, two files are uploaded:

1. **benchmark-results.json** - Complete API response
2. **benchmark-summary.txt** - Human-readable summary

Download from workflow run page → Artifacts section.

## Pricing

- **Free tier:** 10 benchmarks/month
- **Pro:** $29/month, 500 benchmarks
- **Team:** $99/month, unlimited benchmarks

See [benchmark-api.com/pricing](https://benchmark-api.com/pricing)

## FAQ

**Q: How long does a benchmark take?**  
A: Typically 30-60 seconds depending on model count and task complexity.

**Q: Can I benchmark my own prompts?**  
A: Yes! This action works with any code generation prompt.

**Q: What if I hit rate limits?**  
A: Free tier allows 10 benchmarks/month. Upgrade for higher limits or schedule workflows strategically.

**Q: Can I self-host the API?**  
A: Yes, see [deployment docs](https://github.com/yourusername/open-model-benchmark-api#deployment).

**Q: Do you store my prompts?**  
A: Prompts are stored temporarily for benchmark execution. See [privacy policy](https://benchmark-api.com/privacy).

## Support

- 📖 [Full documentation](https://github.com/yourusername/open-model-benchmark-api)
- 💬 [GitHub Discussions](https://github.com/yourusername/open-model-benchmark-api/discussions)
- 🐛 [Report issues](https://github.com/yourusername/open-model-benchmark-api/issues)
- 📧 Email: support@benchmark-api.com

## License

MIT - see [LICENSE](LICENSE)

---

**Like Lighthouse CI, but for AI models.** Make data-driven decisions about which LLM to use.
