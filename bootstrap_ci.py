import numpy as np
import pandas as pd
import json
import os

# bootstrap CI function

def bootstrap_ci(scores, n_bootstrap=10000, ci=0.95):
    means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(scores, size=len(scores), replace=True)
        means.append(np.mean(sample))
    lower = np.percentile(means, (1 - ci) / 2 * 100)
    upper = np.percentile(means, (1 + ci) / 2 * 100)
    return round(lower, 3), round(upper, 3)

# load agreement scores per model pair

def load_scores_by_pair():
    """
    Load results JSON files and separate scores by model pair.
    You need three lists:
    - groq_vs_hf scores
    - groq_vs_groq2 scores  
    - hf_vs_groq2 scores
    """
    results_dir = "results"
    pairs = {
        "groq_vs_hf": [],
        "groq_vs_groq2": [],
        "hf_vs_groq2": [],
    }

    if not os.path.isdir(results_dir):
        return pairs

    for filename in os.listdir(results_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(results_dir, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        pairwise = data.get("pairwise_comparison", {})
        for pair_name in pairs:
            score = pairwise.get(pair_name, {}).get("overall_agreement")
            if isinstance(score, (int, float)):
                pairs[pair_name].append(float(score))

    return pairs


def load_score_by_pair():
    """Backward-compatible alias for singular function name."""
    return load_scores_by_pair()

# main
if __name__ == "__main__":
    pairs = load_scores_by_pair()
    
    for pair_name, scores in pairs.items():
        mean = round(np.mean(scores), 3)
        lower, upper = bootstrap_ci(scores)
        print(f"{pair_name}: mean={mean}, 95% CI=[{lower}, {upper}]")