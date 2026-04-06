import json
import os
import matplotlib.pyplot as plt
import numpy as np
import csv

RESULTS_DIR = "results"


def load_all_results():
    results = []
    for filename in os.listdir(RESULTS_DIR):
        if filename.endswith(".json"):
            path = os.path.join(RESULTS_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    results.append(json.load(f))
            except Exception as e:
                print(f"⚠ Skipping {filename}: {e}")
    return results


def compute_stats(results):
    stats = {
        "total_functions": len(results),
        "overall_agreement": [],
        "preconditions_agreement": [],
        "postconditions_agreement": [],
        "edge_cases_agreement": [],
        "by_module": {},
        "function_scores": []
    }

    for r in results:
        comp = r.get("comparison", {})
        fn_name = r.get("function", "unknown")

        if not comp:
            continue

        module = fn_name.split(".")[0]

        overall = comp.get("overall_agreement", 0)
        pre = comp.get("preconditions", {}).get("agreement_score", 0)
        post = comp.get("postconditions", {}).get("agreement_score", 0)
        edge = comp.get("edge_cases", {}).get("agreement_score", 0)

        stats["overall_agreement"].append(overall)
        stats["preconditions_agreement"].append(pre)
        stats["postconditions_agreement"].append(post)
        stats["edge_cases_agreement"].append(edge)

        stats["function_scores"].append((fn_name, overall))

        if module not in stats["by_module"]:
            stats["by_module"][module] = []
        stats["by_module"][module].append(overall)

    return stats


def print_summary(stats):
    print("=" * 60)
    print("LLM CONTRACT GENERATION AGREEMENT ANALYSIS")
    print("=" * 60)

    print(f"\nTotal functions analyzed: {stats['total_functions']}")

    print("\n--- AGREEMENT RATES ---")
    for field in ["overall", "preconditions", "postconditions", "edge_cases"]:
        scores = stats[f"{field}_agreement"]

        if scores:
            avg = np.mean(scores)
            std = np.std(scores)
            print(f"  {field:20s}: {avg:.2f} ± {std:.2f}  |  "
                  f"min: {min(scores):.2f}  max: {max(scores):.2f}")
        else:
            print(f"  {field:20s}: No data")

    print("\n--- AGREEMENT BY MODULE ---")
    for module, scores in stats["by_module"].items():
        if scores:
            avg = np.mean(scores)
            print(f"  {module:15s}: {avg:.2f} avg ({len(scores)} functions)")

    # distribution
    all_scores = stats["overall_agreement"]
    high = sum(1 for s in all_scores if s >= 0.7)
    medium = sum(1 for s in all_scores if 0.3 <= s < 0.7)
    low = sum(1 for s in all_scores if s < 0.3)

    print(f"\n--- AGREEMENT DISTRIBUTION ---")
    print(f"  High agreement (≥0.7):     {high} functions")
    print(f"  Medium agreement (0.3-0.7): {medium} functions")
    print(f"  Low agreement (<0.3):      {low} functions")

    # best & worst functions
    sorted_scores = sorted(stats["function_scores"], key=lambda x: x[1])

    print("\n--- WORST AGREEMENT FUNCTIONS ---")
    for fn, score in sorted_scores[:5]:
        print(f"  {fn}: {score:.2f}")

    print("\n--- BEST AGREEMENT FUNCTIONS ---")
    for fn, score in sorted_scores[-5:]:
        print(f"  {fn}: {score:.2f}")


def plot_results(stats):
    os.makedirs("results/figures", exist_ok=True)

    # plot 1: agreement by field
    fields = ["preconditions", "postconditions", "edge_cases"]
    avgs = [np.mean(stats[f"{f}_agreement"]) for f in fields]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(fields, avgs)
    plt.ylim(0, 1.0)
    plt.title("LLM Agreement Rate by Contract Field")
    plt.ylabel("Average Agreement Score")
    plt.xlabel("Contract Field")

    for bar, val in zip(bars, avgs):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                 f"{val:.2f}", ha="center")

    plt.tight_layout()
    plt.savefig("results/figures/agreement_by_field.png", dpi=150)
    plt.close()
    print("\n📊 Saved: agreement_by_field.png")

    # plot 2: agreement by module
    modules = list(stats["by_module"].keys())
    module_avgs = [np.mean(stats["by_module"][m]) for m in modules]

    plt.figure(figsize=(10, 5))
    bars = plt.bar(modules, module_avgs)
    plt.ylim(0, 1.0)
    plt.title("LLM Agreement Rate by Python Module")
    plt.ylabel("Average Agreement Score")
    plt.xlabel("Module")

    for bar, val in zip(bars, module_avgs):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                 f"{val:.2f}", ha="center")

    plt.tight_layout()
    plt.savefig("results/figures/agreement_by_module.png", dpi=150)
    plt.close()
    print("📊 Saved: agreement_by_module.png")

    # plot 3: distribution
    plt.figure(figsize=(8, 5))
    plt.hist(stats["overall_agreement"], bins=10, range=(0, 1))
    plt.title("Distribution of Overall Agreement Scores")
    plt.xlabel("Agreement Score")
    plt.ylabel("Number of Functions")

    plt.tight_layout()
    plt.savefig("results/figures/agreement_distribution.png", dpi=150)
    plt.close()
    print("📊 Saved: agreement_distribution.png")


def save_outputs(stats):
    # json summary
    summary = {
        "total_functions": stats["total_functions"],
        "overall_avg": float(np.mean(stats["overall_agreement"])),
        "preconditions_avg": float(np.mean(stats["preconditions_agreement"])),
        "postconditions_avg": float(np.mean(stats["postconditions_agreement"])),
        "edge_cases_avg": float(np.mean(stats["edge_cases_agreement"])),
        "by_module": {
            m: float(np.mean(v))
            for m, v in stats["by_module"].items()
        }
    }

    with open("results/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n💾 Saved: results/summary.json")

    # csv export
    with open("results/results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["function", "overall_agreement"])

        for fn, score in stats["function_scores"]:
            writer.writerow([fn, score])

    print("💾 Saved: results/results.csv")


if __name__ == "__main__":
    print("Loading results...")
    results = load_all_results()

    stats = compute_stats(results)
    print_summary(stats)
    plot_results(stats)
    save_outputs(stats)