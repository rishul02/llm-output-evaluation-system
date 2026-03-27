import json
import re
import os


def parse_contract(llm_output: str) -> dict:
    """
    Safely parse LLM output into a contract dict.
    Handles markdown fences, whitespace, and malformed JSON.
    """
    cleaned = re.sub(r"```(?:json)?", "", llm_output).strip()

    try:
        contract = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse contract JSON:\n{e}\nRaw:\n{cleaned}")

    required_keys = {"preconditions", "postconditions", "edge_cases"}
    missing = required_keys - set(contract.keys())

    if missing:
        raise ValueError(f"Contract missing keys: {missing}")

    return contract


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    
    # word-level normalization
    replacements = {
        r'\blst\b': 'list',
        r'\bint\b': 'integer',
        r'\bstr\b': 'string'
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    text = re.sub(r"\s+", " ", text)
    return text


def build_normalized_map(items):
    """
    Create mapping: normalized_text -> original_text
    """
    return {normalize(item): item for item in items}



def compare_lists(list_a, list_b):
    """
    Compare two lists of contract statements.
    Returns structured comparison.
    """
    map_a = build_normalized_map(list_a)
    map_b = build_normalized_map(list_b)

    keys_a = set(map_a.keys())
    keys_b = set(map_b.keys())

    agreed_keys = keys_a & keys_b
    only_a_keys = keys_a - keys_b
    only_b_keys = keys_b - keys_a

    total_unique = len(keys_a | keys_b)
    agreement_score = len(agreed_keys) / total_unique if total_unique > 0 else 1.0

    return {
        "agreed": [map_a[k] for k in agreed_keys],
        "groq_only": [map_a[k] for k in only_a_keys],
        "hf_only": [map_b[k] for k in only_b_keys],
        "agreement_score": round(agreement_score, 2)
    }


def compare_contracts(contract_a: dict, contract_b: dict) -> dict:
    """
    Compare full contracts across all sections.
    """
    report = {}

    for field in ["preconditions", "postconditions", "edge_cases"]:
        report[field] = compare_lists(
            contract_a.get(field, []),
            contract_b.get(field, [])
        )


    report["overall_agreement"] = round(
        sum(report[f]["agreement_score"] for f in ["preconditions", "postconditions", "edge_cases"]) / 3,
        2
    )

    return report



def save_report(function_name: str, report: dict):
    """
    Save comparison report as JSON file.
    """
    os.makedirs("results", exist_ok=True)

    path = f"results/{function_name}.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Saved report to {path}")



def print_report(function_name: str, report: dict):
    print(f"\n{'='*60}")
    print(f"FUNCTION: {function_name}")
    print(f"Overall Agreement Score: {report['overall_agreement']}")
    print(f"{'='*60}")

    for field in ["preconditions", "postconditions", "edge_cases"]:
        data = report[field]
        print(f"\n--- {field.upper()} (agreement: {data['agreement_score']}) ---")

        if data["agreed"]:
            print("  ✓ BOTH AGREE:")
            for item in data["agreed"]:
                print(f"     - {item}")

        if data["groq_only"]:
            print("  △ GROQ ONLY:")
            for item in data["groq_only"]:
                print(f"     - {item}")

        if data["hf_only"]:
            print("  ◇ HF ONLY:")
            for item in data["hf_only"]:
                print(f"     - {item}")


if __name__ == "__main__":
    groq_raw = """
    {
      "preconditions": ["Input must be a list"],
      "postconditions": [
        "Output will be a list",
        "Output list will not contain duplicate elements",
        "Order of elements in the output list may be different from the input list"
      ],
      "edge_cases": [
        "If input list is empty, output will be an empty list",
        "If input list contains unhashable elements, a TypeError will be raised"
      ]
    }
    """

    hf_raw = """
    {
      "preconditions": ["Input lst must be a list", "Input lst must contain hashable elements"],
      "postconditions": [
        "Output will be a list with no duplicates",
        "Output will be a list with the same length as the input list or less"
      ],
      "edge_cases": [
        "If the input list is empty, the output will be an empty list",
        "If the input list contains only unique elements, the output will be the same as the input list"
      ]
    }
    """

    contract_a = parse_contract(groq_raw)
    contract_b = parse_contract(hf_raw)

    report = compare_contracts(contract_a, contract_b)

    print_report("remove_duplicates", report)
    save_report("remove_duplicates", report)