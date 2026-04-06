import json
import re
import os

from sentence_transformers import SentenceTransformer, util

SIMILARITY_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
SIMILARITY_THRESHOLD = 0.82

import json
import re

def parse_contract(llm_output: str) -> dict:
    """
    Robust parser for LLM JSON output.
    Handles malformed JSON + normalizes structure.
    """

    # remove markdown
    cleaned = re.sub(r"```(?:json)?", "", llm_output).strip()

    # fix hex numbers (0x...) → int
    cleaned = re.sub(r'0x[0-9a-fA-F]+', lambda m: str(int(m.group(0), 16)), cleaned)

    # remove trailing commas
    cleaned = re.sub(r",\s*}", "}", cleaned)
    cleaned = re.sub(r",\s*]", "]", cleaned)

    try:
        contract = json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse contract JSON:\n{cleaned}")

    # ensure required keys
    for key in ["preconditions", "postconditions", "edge_cases"]:
        if key not in contract:
            contract[key] = []

    # to flatten and validate the contract
    for key in ["preconditions", "postconditions", "edge_cases"]:
        if not isinstance(contract[key], list):
            raise ValueError(f"'{key}' must be a list")

        flat = []
        for item in contract[key]:
            if isinstance(item, str):
                flat.append(item)
            elif isinstance(item, dict):
                desc = item.get("description") or item.get("name") or str(item)
                flat.append(desc)
            else:
                flat.append(str(item))

        contract[key] = flat

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
    Compare two lists using semantic similarity.
    Two statements are considered agreed if cosine similarity > threshold.
    """
    if not list_a and not list_b:
        return {"agreed": [], "groq_only": [], "hf_only": [],
                "agreement_score": 1.0}
    if not list_a:
        return {"agreed": [], "groq_only": [], "hf_only": list_b,
                "agreement_score": 0.0}
    if not list_b:
        return {"agreed": [], "groq_only": list_a, "hf_only": [],
                "agreement_score": 0.0}

    # Encode all statements at once — efficient
    embeddings_a = SIMILARITY_MODEL.encode(list_a, convert_to_tensor=True)
    embeddings_b = SIMILARITY_MODEL.encode(list_b, convert_to_tensor=True)

    matched_a = set()
    matched_b = set()
    agreed = []

    # For each statement in A, find best match in B
    for i, emb_a in enumerate(embeddings_a):
        similarities = util.cos_sim(emb_a, embeddings_b)[0]
        best_j = similarities.argmax().item()
        best_score = similarities[best_j].item()

        if best_score >= SIMILARITY_THRESHOLD and best_j not in matched_b:
            agreed.append({
                "groq": list_a[i],
                "hf": list_b[best_j],
                "similarity": round(best_score, 3)
            })
            matched_a.add(i)
            matched_b.add(best_j)

    groq_only = [list_a[i] for i in range(len(list_a)) if i not in matched_a]
    hf_only = [list_b[j] for j in range(len(list_b)) if j not in matched_b]

    total_unique = len(list_a) + len(list_b) - len(agreed)
    agreement_score = len(agreed) / total_unique if total_unique > 0 else 1.0

    return {
        "agreed": agreed,
        "groq_only": groq_only,
        "hf_only": hf_only,
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
                if isinstance(item, dict):
                    print(f"     - {item['groq']}")
                    print(f"       ≈ {item['hf']} (similarity: {item['similarity']})")
                else:
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