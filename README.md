# LLMContractBench

We ask a simple question: if you give two (or three) language models the same Python standard library function and ask for a formal contract (preconditions, postconditions, edge cases), how much do they actually agree?

We find that agreement is generally low, with a clear separation between model pairings. Cross-size comparisons (70B vs 8B) show consistently low agreement, while one same-tier 8B pair shows substantially higher alignment, revealing structure that is not visible from aggregate averages alone.

## What we measured

For each function, we construct a single prompt using its signature, docstring, and source code when available. Three models respond independently with structured JSON contracts.

We compare outputs using Sentence-BERT (`all-MiniLM-L6-v2`) with a fixed similarity threshold of **0.82** to measure semantic agreement across contract fields and overall.

We prioritize SBERT for reproducibility and simplicity: a fixed encoder and fixed threshold without training or LLM-based judging. This makes results easy to reproduce but introduces known limitations in handling paraphrases and fine-grained semantic equivalence.

## Models

| Role | Code key | Provider | Model |
|------|----------|----------|--------|
| Groq 70B | `groq` | Groq | `llama-3.3-70b-versatile` |
| Groq 8B | `groq2` | Groq | `llama-3.1-8b-instant` |
| HF 8B | `hf` | Hugging Face | `Meta-Llama-3-8B-Instruct` |

Pairwise comparisons are reported as: `groq_vs_hf`, `groq_vs_groq2`, `hf_vs_groq2`.

## Majority vote

Majority vote is computed per contract section by exact matching of normalized bullets (casefold + whitespace stripping). A bullet is included if it appears in at least two of three model outputs. No semantic similarity is used here.

## Dataset

**93 functions** from Python’s standard library across six modules: `builtins`, `math`, `statistics`, `functools`, `operator`, and `random`.

Functions are sampled with caps per module and filtered for valid docstrings and inspectable behavior. This ensures ground-truth contracts exist and are interpretable.

## Results

Pairwise agreement (bootstrap 95% CI):

| Pair | Mean | CI |
|------|------|-----|
| Groq 70B vs HF 8B | **0.278** | [0.238, 0.318] |
| Groq 70B vs Groq 8B | **0.274** | [0.234, 0.314] |
| HF 8B vs Groq 8B | **0.600** | [0.547, 0.653] |

Two distinct regimes emerge: low agreement for cross-size comparisons and significantly higher agreement for the HF–Groq 8B pair.

## Contract-level behavior

Preconditions show the highest agreement, likely due to explicit presence in docstrings. Postconditions are moderate, while edge cases consistently show the lowest agreement, reflecting higher variability and hallucination sensitivity.

## Distribution (Groq vs HF pattern)

Most functions fall in the low agreement range, with a small number reaching high agreement. Edge-case reasoning is the least stable component across all models.

## Key observation

Agreement is not uniform across model pairings. The HF–Groq 8B pairing exhibits significantly higher alignment than cross-size comparisons, suggesting that agreement structure depends strongly on model configuration rather than being a global property of LLM behavior.

## Case insight

Low agreement does not necessarily imply incorrect outputs. For functions such as built-in operations, models often produce valid but differently structured or differently abstracted contracts. Semantic similarity captures divergence in expression, not correctness.

## Artifacts

Each run stores:

- raw model outputs
- parsed contracts
- pairwise comparisons
- majority-vote contracts

Analysis scripts compute agreement statistics and bootstrap confidence intervals and generate visualizations.

## Limitations

Semantic similarity is not equivalent to correctness. Results depend on prompt design, model sampling variability, and a fixed snapshot of APIs. The dataset is limited to Python standard library functions, which may not generalize to complex real-world code.

## Repo structure

```
LLMContractBench/
  ├── main.py                  # model inference (Groq + HF)
  ├── collect_functions.py     # dataset construction and prompts
  ├── compare_contracts.py     # SBERT-based agreement scoring
  ├── run_pipeline.py          # full experimental pipeline
  ├── analyze_results.py       # statistics and visualization
  ├── bootstrap_ci.py          # confidence intervals
  ├── functions/functions.json # sampled functions
  ├── evaluation/manual_eval.csv # correctness annotations
  └── results/                 # per-function outputs and aggregated results
```
