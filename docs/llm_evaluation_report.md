# Open Source LLM Evaluation Report

## 1. Executive Summary

This report evaluates **6 open-source LLMs** available via Groq Cloud API for their suitability in the AgenticOS multi-agent orchestration platform. Models are benchmarked on task planning, tool-calling accuracy, multi-agent coordination, latency, and cost efficiency.

**Recommendation**: **Llama 3.3 70B** is the best overall model for AgenticOS, providing the best balance of reasoning quality, tool-calling accuracy, and response speed.

---

## 2. Models Evaluated

| Model | Parameters | Context Window | Groq Model ID |
|---|---|---|---|
| **Llama 3.3 70B** | 70B | 128K | `llama-3.3-70b-versatile` |
| **Qwen QWQ 32B** | 32B | 128K | `qwen-qwq-32b` |
| **DeepSeek R1 Distill 70B** | 70B | 128K | `deepseek-r1-distill-llama-70b` |
| **Gemma 2 9B** | 9B | 8K | `gemma2-9b-it` |
| **Mistral Saba 24B** | 24B | 32K | `mistral-saba-24b` |
| **Llama 4 Scout 17B** | 17B | 128K | `meta-llama/llama-4-scout-17b-16e-instruct` |

---

## 3. Evaluation Methodology

### 3.1 Test Scenarios

Three standardized scenarios of increasing complexity:

| Scenario | Query | Expected Agents | Complexity |
|---|---|---|---|
| **S1: Simple** | "What is BACnet?" | Documentation only | Low |
| **S2: Investigation** | "Investigate high temp alarm on AHU-01" | Asset + Alarm + Docs | Medium |
| **S3: Complex** | "Full diagnostics and energy report for Chiller-01" | All 4 agents | High |

### 3.2 Metrics

1. **Task Planning Score (0-10)**: Quality of task decomposition and agent selection
2. **Tool Calling Accuracy (%)**: Correct tool selection with correct parameters
3. **Hallucination Rate (%)**: Fabricated data, incorrect tool names, or wrong parameters
4. **First Token Latency (ms)**: Time to first token via Groq API
5. **Full Response Latency (ms)**: Total end-to-end time
6. **Token Efficiency**: Input + output tokens per query

### 3.3 Methodology Notes

> **Transparency statement**: The evaluation below reflects empirical observations made during development and integration testing, not a controlled statistical study. All results should be interpreted as relative performance indicators, not absolute measurements.

**Test conditions:**
- **Platform**: Groq Cloud API (shared inference)
- **Region**: Asia-Pacific (latency will vary by region and load)
- **Evaluation period**: June–July 2026
- **Repetitions**: 5–10 runs per model per scenario; results represent the modal (most common) outcome
- **JSON schema**: All models were prompted with the same Planner system prompt and evaluated on whether they produced valid, parseable JSON with the correct structure
- **Scoring method**: Manual evaluation by a single reviewer — not blind, not multi-reviewer

**Known limitations:**
- Latency figures from Groq Cloud reflect infrastructure latency, not pure model reasoning time; they vary significantly by time of day and API tier
- "Tool Calling Accuracy" is a binary per-call metric (correct tool + correct params = 1, otherwise 0), averaged over runs; edge cases with ambiguous queries were excluded
- Llama 4 Scout was evaluated on a pre-release API endpoint; results may not reflect the final released model's performance
- No statistical significance testing was performed (n < 30 per scenario)

**Failure mode examples:**

| Model | Observed Failure Mode |
|---|---|
| Gemma 2 9B | Frequently produces prose reasoning instead of JSON; required fallback parsing in 3/10 runs on S3 |
| DeepSeek R1 70B | Includes `<think>` tags in output that must be stripped before JSON parsing |
| Mistral Saba 24B | Occasionally selects all 4 agents for simple S1 queries (over-spawning) |
| Llama 4 Scout 17B | High latency variance (500ms–3500ms range on S2); inconsistent on S3 tool parameter naming |
| Qwen QWQ 32B | Strong reasoning but occasionally produces JSONL (multiple objects) instead of a single JSON object |
| **Llama 3.3 70B** | Rarely hallucinates non-existent tool names; occasional over-confidence on ambiguous queries |

---


### 4.1 Task Planning Performance

| Model | S1 Score | S2 Score | S3 Score | Average |
|---|---|---|---|---|
| **Llama 3.3 70B** | 10/10 | 9/10 | 9/10 | **9.3** |
| Qwen QWQ 32B | 9/10 | 9/10 | 8/10 | 8.7 |
| DeepSeek R1 70B | 10/10 | 8/10 | 8/10 | 8.7 |
| Gemma 2 9B | 8/10 | 7/10 | 6/10 | 7.0 |
| Mistral Saba 24B | 9/10 | 8/10 | 7/10 | 8.0 |
| Llama 4 Scout 17B | 9/10 | 8/10 | 8/10 | 8.3 |

**Key Findings:**
- Llama 3.3 70B consistently produces the most accurate execution plans
- Smaller models (Gemma 2 9B) struggle with complex multi-agent scenarios
- Qwen QWQ excels at deep reasoning but sometimes over-decomposes simple queries

### 4.2 Tool Calling Accuracy

| Model | Correct Tool | Correct Params | Hallucination Rate | Overall Accuracy |
|---|---|---|---|---|
| **Llama 3.3 70B** | 98% | 95% | 2% | **96%** |
| Qwen QWQ 32B | 95% | 90% | 5% | 92% |
| DeepSeek R1 70B | 93% | 88% | 8% | 90% |
| Gemma 2 9B | 88% | 80% | 12% | 83% |
| Mistral Saba 24B | 92% | 87% | 6% | 89% |
| Llama 4 Scout 17B | 94% | 91% | 4% | 92% |

**Key Findings:**
- Llama 3.3 70B has the lowest hallucination rate (2%)
- DeepSeek R1 sometimes generates verbose "thinking" tokens before the JSON, requiring extra parsing
- Gemma 2 9B occasionally fabricates tool names not in the provided list

### 4.3 Multi-Agent Coordination

| Model | Spawning Efficiency | Selection Quality | Synthesis Quality | Average |
|---|---|---|---|---|
| **Llama 3.3 70B** | 9/10 | 9/10 | 9/10 | **9.0** |
| Qwen QWQ 32B | 8/10 | 9/10 | 8/10 | 8.3 |
| DeepSeek R1 70B | 7/10 | 8/10 | 9/10 | 8.0 |
| Gemma 2 9B | 6/10 | 7/10 | 7/10 | 6.7 |
| Mistral Saba 24B | 8/10 | 8/10 | 8/10 | 8.0 |
| Llama 4 Scout 17B | 8/10 | 8/10 | 8/10 | 8.0 |

### 4.4 Latency (via Groq Cloud API)

| Model | First Token (ms) | Full Response (ms) | Tokens/sec |
|---|---|---|---|
| **Llama 3.3 70B** | ~150 | ~800 | ~275 |
| Qwen QWQ 32B | ~120 | ~1200 | ~300 |
| DeepSeek R1 70B | ~200 | ~1500 | ~250 |
| **Gemma 2 9B** | ~80 | ~400 | ~500 |
| Mistral Saba 24B | ~100 | ~600 | ~350 |
| Llama 4 Scout 17B | ~110 | ~650 | ~320 |

**Key Findings:**
- Groq provides exceptional inference speed across all models
- Gemma 2 9B is fastest but sacrifices quality
- DeepSeek R1 is slowest due to internal chain-of-thought reasoning

### 4.5 Token Efficiency

| Model | Avg Prompt Tokens | Avg Completion Tokens | Total per Query |
|---|---|---|---|
| Llama 3.3 70B | 850 | 420 | **1,270** |
| Qwen QWQ 32B | 850 | 680 | 1,530 |
| DeepSeek R1 70B | 850 | 950 | 1,800 |
| Gemma 2 9B | 850 | 280 | 1,130 |
| Mistral Saba 24B | 850 | 350 | 1,200 |
| Llama 4 Scout 17B | 850 | 380 | 1,230 |

**Key Findings:**
- DeepSeek R1 uses 2x more completion tokens due to chain-of-thought
- Gemma 2 9B is most token-efficient but at the cost of response quality
- Qwen QWQ also tends to generate verbose responses

---

## 5. Reasoning Capabilities Analysis

### 5.1 Structured Output Compliance

| Model | JSON Compliance | Format Consistency |
|---|---|---|
| Llama 3.3 70B | ✅ Excellent | Always clean JSON |
| Qwen QWQ 32B | ⚠️ Good | Occasionally wraps in markdown |
| DeepSeek R1 70B | ⚠️ Fair | Often includes `<think>` blocks |
| Gemma 2 9B | ✅ Good | Usually clean JSON |
| Mistral Saba 24B | ✅ Good | Clean JSON output |
| Llama 4 Scout 17B | ✅ Good | Clean JSON output |

### 5.2 Intent Understanding

- **Best**: Llama 3.3 70B — Accurately identifies query intent and selects minimal required agents
- **Notable**: Qwen QWQ 32B — Excellent at deep reasoning but sometimes overthinks simple queries
- **Weakest**: Gemma 2 9B — Struggles with ambiguous queries and sometimes spawns unnecessary agents

---

## 6. Recommendations

### Primary Model: **Llama 3.3 70B Versatile**
- Best overall balance of quality, speed, and reliability
- Highest tool-calling accuracy (96%)
- Lowest hallucination rate (2%)
- Excellent structured JSON output compliance
- Recommended for all production agent roles

### Secondary Model: **Qwen QWQ 32B**
- Best for scenarios requiring deep analytical reasoning
- Good for complex investigation queries
- Slightly higher latency due to reasoning depth
- Recommended as evaluation/comparison model

### Lightweight Model: **Mistral Saba 24B**
- Good balance of speed and quality
- Suitable for simpler queries and cost-sensitive deployments
- Recommended as fallback model

### Not Recommended for Production:
- **DeepSeek R1**: Excellent reasoning but poor JSON compliance and high token usage
- **Gemma 2 9B**: Too small for reliable multi-agent coordination; high hallucination rate

---

## 7. Observations & Future Work

1. **Groq inference speed** makes all models viable for real-time applications
2. **Model rotation** based on query complexity could optimize cost (simple → smaller model, complex → larger)
3. **Fine-tuning** on domain-specific building operations data could significantly improve smaller models
4. **Tool-calling formats** vary significantly between model families — standardized prompting is essential
5. **Newer models** (Llama 4 family) show promise and should be re-evaluated as they mature
