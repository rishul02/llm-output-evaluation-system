import json
import time
import os

from collect_functions import build_prompt
from main import generate_with_groq, generate_with_hf, generate_with_groq_2
from compare_contracts import parse_contract, compare_contracts


INPUT_PATH = "functions/functions.json"
OUTPUT_DIR = "results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def majority_vote(c1, c2, c3):
    result = {}

    for field in ["preconditions", "postconditions", "edge_cases"]:
        combined = c1[field] + c2[field] + c3[field]

        counts = {}
        for item in combined:
            key = item.lower().strip()
            counts[key] = counts.get(key, 0) + 1

        majority_items = [k for k, v in counts.items() if v >= 2]

        result[field] = majority_items

    return result


def load_functions():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_result(name, data):
    safe_name = name.replace(".", "_")
    path = os.path.join(OUTPUT_DIR, f"{safe_name}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    functions = load_functions()
    print(f"Loaded {len(functions)} functions\n")

    for fn in functions:
        try:
            # 1. build prompt
            prompt = build_prompt(fn)

            # 2. call models
            groq_raw = generate_with_groq(prompt)
            hf_raw = generate_with_hf(prompt)
            groq2_raw = generate_with_groq_2(prompt)

            # 3. parse
            try:
                groq_contract = parse_contract(groq_raw)
            except:
                groq_contract = {"preconditions": [], "postconditions": [], "edge_cases": []}

            try:
                groq2_contract = parse_contract(groq2_raw)
            except:
                groq2_contract = {"preconditions": [], "postconditions": [], "edge_cases": []}

            try:
                hf_contract = parse_contract(hf_raw)
            except:
                hf_contract = {"preconditions": [], "postconditions": [], "edge_cases": []}

            # 4. compare
            comparison = {
                "groq_vs_hf": compare_contracts(groq_contract, hf_contract),
                "groq_vs_groq2": compare_contracts(groq_contract, groq2_contract),
                "hf_vs_groq2": compare_contracts(hf_contract, groq2_contract)
            }

            # 3.5 majority vote
            majority = majority_vote(groq_contract, groq2_contract, hf_contract)

            # 5. save
            result = {
            "function": fn["full_name"],

            "raw_outputs": {
                "groq": groq_raw,
                "groq2": groq2_raw,
                "hf": hf_raw
            },

            "parsed_contracts": {
                "groq": groq_contract,
                "groq2": groq2_contract,
                "hf": hf_contract
            },

            "pairwise_comparison": comparison,

            "majority_contract": majority
        }
            save_result(fn["full_name"], result)

            # 6. success log
            print(f" {fn['full_name']} done")

            # 7. rate limit
            time.sleep(1)

        except Exception as e:
            print(f"{fn['full_name']} failed: {e}")
            continue


if __name__ == "__main__":
    main()