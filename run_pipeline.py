import json
import time
import os

from collect_functions import build_prompt
from main import generate_with_groq, generate_with_hf
from compare_contracts import parse_contract, compare_contracts


INPUT_PATH = "functions/functions.json"
OUTPUT_DIR = "results"

os.makedirs(OUTPUT_DIR, exist_ok=True)


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

            # 3. parse
            groq_contract = parse_contract(groq_raw)
            hf_contract = parse_contract(hf_raw)

            # 4. compare
            comparison = compare_contracts(groq_contract, hf_contract)

            # 5. save
            result = {
                "function": fn["full_name"],
                "groq": groq_contract,
                "hf": hf_contract,
                "comparison": comparison
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