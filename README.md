# LLMContractBench

This project studies how consistently large language models infer code contracts for Python standard library functions.

## Research Question

When two LLMs independently infer the behavior of the same function — in terms of preconditions, postconditions, and edge cases — how often do they agree?

If they disagree, can those disagreements be categorized in a meaningful way, and do they reflect limitations in how LLMs reason about code?

## Models Compared

| Model | Provider | Parameters |
|-------|----------|------------|
| Llama-3.3 70B | Groq | 70B |
| Llama-3 8B | HuggingFace | 8B |

## Dataset

The dataset consists of 53 functions sampled from six Python standard library modules:

builtins, math, statistics, functools, operator, random

## Methodology

For each function, the signature, docstring, and (when available) source code are extracted. The same prompt is then sent to both models, asking them to produce a structured contract in JSON format.

The outputs are parsed and normalized into three categories:
- preconditions
- postconditions
- edge cases

To compare the outputs, sentence-level semantic similarity is computed using Sentence-BERT (all-MiniLM-L6-v2) with a threshold of 0.82. Agreement scores are calculated separately for each category and combined into an overall score.

## Results

The average overall agreement between the two models is 0.30 with a standard deviation of 0.20. This indicates both low agreement and high variability across functions.

Agreement differs significantly across categories:

| Field | Agreement |
|-------|-----------|
| Preconditions | 0.49 |
| Postconditions | 0.29 |
| Edge Cases | 0.11 |

Preconditions show the highest agreement, likely because they are often explicitly stated in docstrings. Edge cases show the lowest agreement, suggesting that they require deeper reasoning that the models do not consistently perform.

Agreement also varies by module:

| Module | Agreement | Functions |
|--------|-----------|-----------|
| math | 0.45 | 10 |
| builtins | 0.30 | 10 |
| functools | 0.28 | 10 |
| statistics | 0.25 | 10 |
| random | 0.26 | 2 |
| operator | 0.21 | 10 |

Functions with clear mathematical behavior tend to produce higher agreement. More abstract or operational functions show lower agreement.

In terms of distribution, most functions fall into the low-agreement range:

- High agreement (≥ 0.7): 1 function  
- Medium agreement (0.3–0.7): 21 functions  
- Low agreement (< 0.3): 30 functions  

The best agreement was observed for functions such as statistics.cosh (0.72), math.comb (0.67), and builtins.abs (0.67). The lowest agreement occurred for builtins.bin (0.00), operator.delitem (0.00), and builtins.any (0.08).

## Case Study: builtins.bin

The function builtins.bin has an overall agreement score of 0.00, even though both models produce reasonable-looking contracts.

Three types of differences are visible here:

- Different terminology is used for the same concept (e.g., "number" vs "x")
- One model introduces incorrect constraints (e.g., limiting output length)
- The models describe behavior at different levels of abstraction (general statements vs specific examples)

This shows that a low agreement score does not necessarily mean complete disagreement. It may reflect differences in wording, level of detail, or occasional hallucinations.

## Disagreement Types

Across the dataset, three recurring patterns appear:

1. Terminology differences: the same idea is expressed using different words or variable names.

2. Abstraction differences: one model describes behavior generally, while the other uses concrete examples.

3. Incorrect statements: one model introduces constraints or assumptions that are not true for the function.

The third category is the most concerning, since it can lead to incorrect conclusions about program behavior.

## Conclusion

Agreement between models on inferred code contracts is generally low. The results suggest that LLMs are more reliable when describing simple, well-defined behavior, but less consistent when reasoning about edge cases or implicit properties.

This has implications for using LLMs in program analysis or documentation. Relying on a single model’s output may not be sufficient, and disagreements between models can be informative.

## Limitations

The evaluation relies on semantic similarity at the sentence level, which may not capture all forms of equivalence. The dataset is relatively small and limited to standard library functions. Results are based on a single prompt and a single run, and do not directly measure correctness.

## Project Structure

LLMContractBench/
  ├── main.py                  # API calls (Groq, HuggingFace)
  ├── collect_functions.py     # function extraction and prompt generation
  ├── compare_contracts.py     # semantic comparison logic
  ├── run_pipeline.py          # full pipeline execution
  ├── analyze_results.py       # analysis and visualization
  ├── functions/
  │   └── functions.json
  ├── results/
  │   ├── *.json
  │   ├── summary.json
  │   ├── results.csv
  │   └── figures/
  └── README.md
