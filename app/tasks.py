from celery import Task
from sqlalchemy.orm import Session
import httpx
import time
import json
from datetime import datetime

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Benchmark, BenchmarkResult, BenchmarkStatus
from app.config import settings


# Models to benchmark (expandable)
BENCHMARK_MODELS = [
    "qwen/qwen-2.5-coder-32b-instruct",
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-large-2407",
    "deepseek/deepseek-coder-v2",
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "google/gemini-pro-1.5",
    "cohere/command-r-plus",
]


class DatabaseTask(Task):
    _db: Session = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def run_benchmark(self, benchmark_id: str):
    """Execute benchmark across all models"""
    db = self.db
    
    # Get benchmark
    benchmark = db.query(Benchmark).filter(Benchmark.benchmark_id == benchmark_id).first()
    if not benchmark:
        return {"error": "Benchmark not found"}
    
    benchmark.status = BenchmarkStatus.RUNNING
    db.commit()
    
    results = []
    
    for model_name in BENCHMARK_MODELS:
        try:
            result = _run_single_model_benchmark(
                model_name=model_name,
                task=benchmark.task,
                expected_output=benchmark.expected_output,
                test_cases=benchmark.test_cases
            )
            
            # Save result to DB
            db_result = BenchmarkResult(
                benchmark_id=benchmark.id,
                model_name=model_name,
                model_output=result["output"],
                accuracy=result["accuracy"],
                cost_usd=result["cost_usd"],
                latency_ms=result["latency_ms"],
                passed_tests=result["passed_tests"],
                total_tests=result["total_tests"],
                confidence_score=result["confidence_score"],
                error_message=result.get("error")
            )
            db.add(db_result)
            results.append(result)
            
        except Exception as e:
            db_result = BenchmarkResult(
                benchmark_id=benchmark.id,
                model_name=model_name,
                accuracy=0.0,
                cost_usd=0.0,
                latency_ms=0,
                passed_tests=0,
                total_tests=0,
                confidence_score=0.0,
                error_message=str(e)
            )
            db.add(db_result)
    
    benchmark.status = BenchmarkStatus.COMPLETED
    benchmark.completed_at = datetime.utcnow()
    db.commit()
    
    return {"benchmark_id": benchmark_id, "results": len(results)}


def _run_single_model_benchmark(model_name: str, task: str, expected_output: str = None, test_cases: list = None) -> dict:
    """Run benchmark on a single model via OpenRouter"""
    
    start_time = time.time()
    
    # Call OpenRouter API
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://open-model-benchmark-api.com",
        "X-Title": "Open Model Benchmark API"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful coding assistant. Provide only the code solution, no explanations unless asked."
            },
            {
                "role": "user",
                "content": task
            }
        ]
    }
    
    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        
        latency_ms = int((time.time() - start_time) * 1000)
        output = data["choices"][0]["message"]["content"]
        
        # Calculate cost (from OpenRouter usage data)
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        # Rough cost estimation (varies by model, these are averages)
        cost_per_1k_prompt = 0.0003  # $0.30 per 1M tokens
        cost_per_1k_completion = 0.0006
        cost_usd = (prompt_tokens * cost_per_1k_prompt / 1000) + (completion_tokens * cost_per_1k_completion / 1000)
        
        # Calculate accuracy
        accuracy = 0.0
        passed_tests = 0
        total_tests = 0
        
        if expected_output:
            # Simple string similarity
            accuracy = _calculate_similarity(output, expected_output)
        
        if test_cases:
            total_tests = len(test_cases)
            # In production, would execute test cases in sandbox
            # For now, simple heuristic: check if expected values appear in output
            for test_case in test_cases:
                if test_case.get("expected", "") in output:
                    passed_tests += 1
            
            if total_tests > 0:
                test_accuracy = passed_tests / total_tests
                accuracy = max(accuracy, test_accuracy)
        
        # Confidence score (based on response completeness)
        confidence_score = min(1.0, len(output) / 500)  # Simple heuristic
        
        return {
            "output": output,
            "accuracy": round(accuracy, 3),
            "cost_usd": round(cost_usd, 6),
            "latency_ms": latency_ms,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "confidence_score": round(confidence_score, 2)
        }
        
    except Exception as e:
        return {
            "output": None,
            "accuracy": 0.0,
            "cost_usd": 0.0,
            "latency_ms": 0,
            "passed_tests": 0,
            "total_tests": 0,
            "confidence_score": 0.0,
            "error": str(e)
        }


def _calculate_similarity(text1: str, text2: str) -> float:
    """Simple character-level similarity (production would use AST comparison)"""
    if not text1 or not text2:
        return 0.0
    
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    
    if text1 == text2:
        return 1.0
    
    # Jaccard similarity on words
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0
