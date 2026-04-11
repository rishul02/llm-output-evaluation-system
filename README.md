# LLMContractBench

We ask a simple question: if you hand two (or three) language models the same Python stdlib function and ask for a formal contract — preconditions, postconditions, edge cases — **how much do they actually agree?**

Spoiler: not much, especially when you compare models across providers and sizes. But the spread tells a story, and this repo is the machinery plus the numbers we got on one full pass.

We went in expecting the messy part to be “70B vs 8B” or “Groq vs Hugging Face.” What we actually saw was subtler: the **pair of 8B endpoints** separated from the cross-size pairs in a way that a single headline number would have hidden.

## What we measured

For each function we build one prompt from the signature, docstring, and source when available. Three models answer independently. We parse JSON contracts, compare them with sentence-level semantic similarity (Sentence-BERT, `all-MiniLM-L6-v2`, threshold **0.82**), and record agreement per section and overall.

We chose SBERT for **simplicity and reproducibility** over training a custom similarity scorer or an LLM-as-judge: fixed encoder, fixed threshold, no extra tuning loop. The tradeoff is familiar — it is cheap to run and easy to describe in a paper, but it will treat some paraphrases as disagreement and occasionally treat near-duplicates as agreement.

**New in this version:** we run **three** models, not two — so you get **three pairwise comparisons**, a **majority vote** over parsed contract bullets (defined below), and **defensive parsing** so one bad response does not kill the whole run.

## Models (naming)

We use one label everywhere in prose; **code and JSON keys** keep shorter names for compatibility.

| Role (README) | In code / JSON | Provider | Model id |
|---------------|----------------|----------|----------|
| **Groq 70B** | `groq` | Groq | `llama-3.3-70b-versatile` |
| **Groq 8B (Instant)** | `groq2` | Groq | `llama-3.1-8b-instant` |
| **HF 8B** | `hf` | Hugging Face Inference | `meta-llama/Meta-Llama-3-8B-Instruct` |

Pairwise comparisons in `results/*.json` use the keys `groq_vs_hf`, `groq_vs_groq2`, and `hf_vs_groq2` — here **`groq2` always means Groq 8B (Instant)**, not a second 70B run.

## Majority vote (reproducible)

Short version: pairwise similarity is fuzzy; majority vote is deliberately blunt.

**Pairwise agreement** uses SBERT similarity as above.

**Majority vote** is separate: for each section (`preconditions`, `postconditions`, `edge_cases`), we concatenate the three models’ bullet lists, normalize each bullet with **casefold + strip whitespace**, count occurrences, and **keep a bullet if it appears at least twice** (two of three models). There is **no** SBERT step in majority vote — only exact match after that normalization. Wording variants that differ only in capitalization or outer spaces are merged; paraphrases are not.

## Dataset

**93 functions** across six standard library modules: `builtins`, `math`, `statistics`, `functools`, `operator`, `random`. Sampling is capped per module in `collect_functions.py` (currently up to **20** functions per module, with a skip list for unhelpful builtins). Sticking to the stdlib keeps the task grounded: real docstrings, real edge cases people argue about in reviews.

Function names in outputs follow **`module.function`** (e.g. `builtins.bin` is the stdlib `bin` built-in, not a module named `builtins.bin`).

## What the numbers said (this run)

On **per-function overall agreement** aggregated from `results/*.json`:

| Pair | Mean agreement | 95% bootstrap CI |
|------|----------------|------------------|
| Groq 70B vs HF 8B | **0.278** | [0.238, 0.318] |
| Groq 70B vs Groq 8B (Instant) | **0.274** | [0.234, 0.314] |
| HF 8B vs Groq 8B (Instant) | **0.60** | [0.547, 0.653] |

The first two pairs sit in the same ballpark — rough, noisy agreement in the high twenties. The **two 8B models** (HF vs Groq 8B Instant) land near **0.6**. **That split is the main empirical observation in this run** — we do not attribute it to a single cause: it could reflect model family, provider, decoding, temperature, or interaction effects; isolating those would need controlled follow-up experiments. Interestingly, if you had only plotted “Groq 70B vs HF 8B,” you might conclude the whole benchmark is uniformly noisy; the HF–Groq 8B pair shows there is more structure than that.

**By contract section** (averages over pairs and functions):

- **Preconditions** land highest — often anchored in the docstring.
- **Postconditions** sit in the middle.
- **Edge cases** trail behind — more room for invention, omission, or hallucination.

Rough section-level means from the same run look like: preconditions ~0.45–0.76 depending on pair, postconditions ~0.23–0.58, edge cases ~0.13–0.45 (HF vs Groq 8B Instant is consistently the tightest pair).

**Distribution** (same thresholds as `analyze_results.py`: high > 0.75, medium > 0.4): for the cross-size / cross-provider pairs, most functions sit in the **low** bucket; for HF 8B vs Groq 8B (Instant), a solid chunk hits **high**.

Examples of **low mean agreement across the three pairs** (for each function: average of `groq_vs_hf`, `groq_vs_groq2`, and `hf_vs_groq2` — i.e. mean of the three `overall_agreement` values in `pairwise_comparison`): `operator.contains` (0.0), `builtins.bin`, `builtins.hex`, several `operator.*` helpers — where wording and abstraction levels diverge.

## Case study: why “low agreement” is not always “both wrong”

Take something like `builtins.bin`: both models can sound plausible while disagreeing on wording, level of detail, or an extra constraint. Semantic similarity catches *misalignment*, not *ground truth*. For that we maintain a small **human-labeled** sheet in `evaluation/manual_eval.csv` (correctness-style notes, not just similarity).

## Artifacts

Each pipeline run writes one JSON per function under `results/`, including:

- `raw_outputs` from all three models (`groq`, `groq2`, `hf`)
- `parsed_contracts`
- `pairwise_comparison` (`groq_vs_hf`, `groq_vs_groq2`, `hf_vs_groq2`)
- `majority_contract`

`analyze_results.py` loads those files and writes figures under `results/figures/`. `bootstrap_ci.py` loads agreement scores by pair and prints bootstrap confidence intervals — useful when you want a single line for a paper or slide.

## Limitations

Similarity is not proof of correctness. One prompt, one temperature setting, one snapshot of APIs — rerun and you will see drift. The stdlib subset is still a slice of real-world code.

None of that makes the agreement scores meaningless; it just means they are **benchmark-relative**, not a claim about universal LLM behavior.

## Repo layout

```
LLMContractBench/
  ├── main.py                  # Groq + Hugging Face API calls
  ├── collect_functions.py     # Sampling + prompt building
  ├── compare_contracts.py     # Parse + SBERT comparison
  ├── run_pipeline.py          # End-to-end: 3 models, compare, majority vote
  ├── analyze_results.py       # Aggregates, plots, disagreement lists
  ├── bootstrap_ci.py          # Per-pair means + bootstrap CIs
  ├── functions/functions.json
  ├── evaluation/manual_eval.csv
  ├── results/*.json           # Per-function outputs
  ├── results/summary.json     # Optional aggregate snapshot
  ├── results/results.csv
  └── results/figures/
```

---

**Bottom line:** inferred contracts are a fragile common ground between LLMs. If you care about reliability, compare models, look at sections separately, and do not trust edge-case lists without a second opinion — human or machine.
