#!/bin/bash
set -e

echo "🚀 Starting Open Model Benchmark..."

# Validate required inputs
if [ -z "$API_KEY" ]; then
  echo "❌ Error: api_key is required"
  exit 1
fi

if [ -z "$TASK_NAME" ] || [ -z "$CODE_PROMPT" ]; then
  echo "❌ Error: task_name and code_prompt are required"
  exit 1
fi

# Prepare JSON payload
PAYLOAD=$(jq -n \
  --arg name "$TASK_NAME" \
  --arg desc "$TASK_DESCRIPTION" \
  --arg prompt "$CODE_PROMPT" \
  --arg expected "$EXPECTED_OUTPUT" \
  --arg category "$TASK_CATEGORY" \
  --arg models "$MODELS" \
  '{
    name: $name,
    description: $desc,
    code_prompt: $prompt,
    expected_output: $expected,
    task_category: $category,
    models: ($models | split(","))
  }')

echo "📤 Submitting benchmark to $API_ENDPOINT/v1/benchmark..."
echo "Models: $MODELS"

# Submit benchmark
RESPONSE=$(curl -s -X POST "$API_ENDPOINT/v1/benchmark" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# Check for errors
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
  ERROR=$(echo "$RESPONSE" | jq -r '.detail')
  echo "❌ API Error: $ERROR"
  exit 1
fi

# Extract benchmark ID
BENCHMARK_ID=$(echo "$RESPONSE" | jq -r '.benchmark_id // empty')

if [ -z "$BENCHMARK_ID" ]; then
  echo "❌ Failed to get benchmark ID from response"
  echo "$RESPONSE"
  exit 1
fi

echo "✅ Benchmark submitted: $BENCHMARK_ID"
echo "⏳ Waiting for results (this may take 30-60 seconds)..."

# Poll for results (max 3 minutes)
MAX_ATTEMPTS=36
ATTEMPT=0
RESULTS=""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  sleep 5
  ATTEMPT=$((ATTEMPT + 1))
  
  RESULTS=$(curl -s -X GET "$API_ENDPOINT/v1/benchmark/$BENCHMARK_ID" \
    -H "Authorization: Bearer $API_KEY")
  
  STATUS=$(echo "$RESULTS" | jq -r '.status // "pending"')
  
  if [ "$STATUS" = "completed" ]; then
    echo "✅ Benchmark completed!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "❌ Benchmark failed"
    echo "$RESULTS" | jq -r '.error // "Unknown error"'
    exit 1
  fi
  
  echo "  Status: $STATUS (attempt $ATTEMPT/$MAX_ATTEMPTS)"
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo "❌ Timeout waiting for results"
  exit 1
fi

# Save full results
echo "$RESULTS" > benchmark-results.json

# Extract key metrics
BEST_MODEL=$(echo "$RESULTS" | jq -r '.results | sort_by(-.accuracy) | .[0].model')
BEST_ACCURACY=$(echo "$RESULTS" | jq -r '.results | sort_by(-.accuracy) | .[0].accuracy')
BEST_COST=$(echo "$RESULTS" | jq -r '.results | sort_by(-.accuracy) | .[0].cost_usd')
SUMMARY=$(echo "$RESULTS" | jq -r '.summary // "No summary available"')
RESULTS_URL="$API_ENDPOINT/v1/benchmark/$BENCHMARK_ID"

# Set outputs for GitHub Actions
echo "benchmark_id=$BENCHMARK_ID" >> $GITHUB_OUTPUT
echo "best_model=$BEST_MODEL" >> $GITHUB_OUTPUT
echo "best_accuracy=$BEST_ACCURACY" >> $GITHUB_OUTPUT
echo "best_cost=$BEST_COST" >> $GITHUB_OUTPUT
echo "results_url=$RESULTS_URL" >> $GITHUB_OUTPUT
echo "results_json<<EOF" >> $GITHUB_OUTPUT
echo "$RESULTS" >> $GITHUB_OUTPUT
echo "EOF" >> $GITHUB_OUTPUT

# Create summary text
cat > benchmark-summary.txt <<EOF
==============================================
Open Model Benchmark Results
==============================================

Task: $TASK_NAME
Benchmark ID: $BENCHMARK_ID

Best Model: $BEST_MODEL
Accuracy: $(echo "$BEST_ACCURACY * 100" | bc)%
Cost: \$$(printf "%.4f" "$BEST_COST")

Summary: $SUMMARY

Full Results URL: $RESULTS_URL
==============================================
EOF

cat benchmark-summary.txt

# Display results table
echo ""
echo "📊 Detailed Results:"
echo "$RESULTS" | jq -r '
  .results | 
  ["Model", "Accuracy", "Latency", "Cost", "Tokens"] as $headers |
  ([$headers] + 
   map([.model, (.accuracy * 100 | tostring + "%"), (.latency_ms | tostring + "ms"), ("$" + (.cost_usd | tostring)), .tokens_used | tostring])) |
  .[] | @tsv
' | column -t -s $'\t'

# Check failure threshold
if [ "$(echo "$BEST_ACCURACY < $FAIL_THRESHOLD" | bc -l)" -eq 1 ]; then
  echo ""
  echo "❌ Best model accuracy ($BEST_ACCURACY) is below threshold ($FAIL_THRESHOLD)"
  exit 1
fi

echo ""
echo "✅ Benchmark completed successfully!"
