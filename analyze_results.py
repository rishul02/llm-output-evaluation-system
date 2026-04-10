import os
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

RESULTS_DIR = "results"
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")


# load

def load_results():
    data = []
    for file in os.listdir(RESULTS_DIR):
        if file.endswith(".json"):
            try:
                with open(os.path.join(RESULTS_DIR, file), "r", encoding="utf-8") as f:
                    data.append(json.load(f))
            except Exception as e:
                print(f" Failed to load {file}: {e}")
    return data


# extraction

def extract_overall_scores(results):
    scores = {
        "groq_vs_hf": [],
        "groq_vs_groq2": [],
        "hf_vs_groq2": []
    }

    for r in results:
        try:
            comp = r["pairwise_comparison"]

            scores["groq_vs_hf"].append(comp["groq_vs_hf"]["overall_agreement"])
            scores["groq_vs_groq2"].append(comp["groq_vs_groq2"]["overall_agreement"])
            scores["hf_vs_groq2"].append(comp["hf_vs_groq2"]["overall_agreement"])
        except Exception as e:
            print(f" Skipping bad entry: {e}")

    return scores


def compute_average(scores):
    return {k: round(sum(v)/len(v), 3) if v else 0 for k, v in scores.items()}


def agreement_distribution(scores):
    dist = defaultdict(lambda: {"high": 0, "medium": 0, "low": 0})

    for k, values in scores.items():
        for v in values:
            if v > 0.75:
                dist[k]["high"] += 1
            elif v > 0.4:
                dist[k]["medium"] += 1
            else:
                dist[k]["low"] += 1

    return dist


def section_wise_analysis(results):
    sections = ["preconditions", "postconditions", "edge_cases"]
    section_scores = defaultdict(list)

    for r in results:
        try:
            comp = r["pairwise_comparison"]

            for pair in comp:
                for sec in sections:
                    score = comp[pair][sec]["agreement_score"]
                    section_scores[(pair, sec)].append(score)
        except Exception as e:
            print(f"Skipping section error: {e}")

    avg_section = {}
    for key, vals in section_scores.items():
        avg_section[key] = round(sum(vals)/len(vals), 3) if vals else 0

    return avg_section


def majority_strength(results):
    counts = []

    for r in results:
        try:
            majority = r["majority_contract"]
            size = sum(len(majority[k]) for k in majority)
            counts.append(size)
        except:
            continue

    return round(sum(counts)/len(counts), 2) if counts else 0


def find_disagreements(results, threshold=0.5):
    bad_cases = []

    for r in results:
        try:
            comp = r["pairwise_comparison"]

            avg = (
                comp["groq_vs_hf"]["overall_agreement"] +
                comp["groq_vs_groq2"]["overall_agreement"] +
                comp["hf_vs_groq2"]["overall_agreement"]
            ) / 3

            if avg < threshold:
                fn = r.get("function") or r.get("function_name", "unknown")
                bad_cases.append((fn, round(avg, 2)))

        except:
            continue

    return sorted(bad_cases, key=lambda x: x[1])


# visualization

def plot_heatmap(section_scores):
    pairs = ["groq_vs_hf", "groq_vs_groq2", "hf_vs_groq2"]
    sections = ["preconditions", "postconditions", "edge_cases"]

    matrix = []

    for pair in pairs:
        row = []
        for sec in sections:
            val = section_scores.get((pair, sec), 0)
            row.append(val)
        matrix.append(row)

    plt.figure(figsize=(8, 5))
    sns.heatmap(
        matrix,
        annot=True,
        xticklabels=sections,
        yticklabels=pairs,
        cmap="YlGnBu",
        vmin=0,
        vmax=1
    )

    plt.title("Section-wise Agreement Heatmap")
    plt.savefig(os.path.join(FIGURES_DIR, "heatmap.png"))
    plt.close()


def plot_boxplot(scores):
    data = []
    labels = []

    for k, vals in scores.items():
        data.extend(vals)
        labels.extend([k] * len(vals))

    plt.figure(figsize=(8, 5))
    sns.boxplot(x=labels, y=data)

    plt.title("Agreement Score Distribution")
    plt.xlabel("Model Pairs")
    plt.ylabel("Agreement Score")

    plt.savefig(os.path.join(FIGURES_DIR, "boxplot.png"))
    plt.close()


# main

def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)

    results = load_results()
    print(f"Loaded {len(results)} results")

    # 1. overall
    scores = extract_overall_scores(results)
    avg_scores = compute_average(scores)

    print("\n=== Average Agreement ===")
    for k, v in avg_scores.items():
        print(f"{k}: {v}")

    # 2. distribution
    dist = agreement_distribution(scores)

    print("\n=== Distribution ===")
    for pair, d in dist.items():
        print(f"{pair}: {d}")

    # 3. section-wise
    section_scores = section_wise_analysis(results)

    print("\n=== Section-wise ===")
    for k, v in section_scores.items():
        print(f"{k}: {v}")

    # 4. majority
    majority_avg = majority_strength(results)
    print(f"\n=== Avg Majority Size: {majority_avg} ===")

    # 5. disagreements
    bad = find_disagreements(results, threshold=0.5)

    print("\n=== Low Agreement Cases ===")
    for fn, score in bad[:10]:
        print(fn, score)

    # plots
    plot_heatmap(section_scores)
    plot_boxplot(scores)

    print("\nPlots saved in results/figures/")


if __name__ == "__main__":
    main()