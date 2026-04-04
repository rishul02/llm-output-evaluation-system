import inspect
import json
import os

import builtins
import math
import statistics
import functools
import operator
import random

# modules to scan
MODULES = {
    "builtins": builtins,
    "math": math,
    "statistics": statistics,
    "functools": functools,
    "operator": operator,
    "random": random,
}

MAX_FUNCTIONS_PER_MODULE = 10

# skip low-value / weird functions
SKIP_FUNCTIONS = {
    "aiter", "anext", "breakpoint", "help", "exit", "quit"
}


# extract function info
def get_function_info(obj, module_name):
    try:
        sig = str(inspect.signature(obj))
    except (ValueError, TypeError):
        sig = "()"

    doc = inspect.getdoc(obj)
    if not doc:
        return None

    # clean docstring
    doc = doc.strip().split("\n")[0][:150]

    # get source if available
    try:
        source = inspect.getsource(obj)
    except (OSError, TypeError):
        source = None

    # fallback input text
    input_text = source if source else doc

    return {
        "name": obj.__name__,
        "module": module_name,
        "signature": sig,
        "doc": doc,
        "source": source,
        "input_text": input_text,
        "full_name": f"{module_name}.{obj.__name__}"
    }


# extract functions from module
def get_functions_from_module(module, module_name, max_per_module):
    functions = []

    for name, obj in inspect.getmembers(module):

        if name.startswith("_") or name in SKIP_FUNCTIONS:
            continue

        if not (inspect.isbuiltin(obj) or inspect.isfunction(obj)):
            continue

        # extra filter to remove classes explicitly
        if isinstance(obj, type):
            continue

        info = get_function_info(obj, module_name)
        if not info:
            continue

        functions.append(info)

        if len(functions) >= max_per_module:
            break

    return functions


# collect all functions
def collect_all_functions():
    all_functions = []

    print("Collecting functions...\n")

    for module_name, module in MODULES.items():
        funcs = get_functions_from_module(
            module,
            module_name,
            MAX_FUNCTIONS_PER_MODULE
        )

        all_functions.extend(funcs)
        print(f"{module_name}: {len(funcs)} functions collected")

    return all_functions


# save to file
def save_functions(functions):
    os.makedirs("functions", exist_ok=True)

    path = "functions/functions.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(functions, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved {len(functions)} functions to {path}")


# preview functions
def preview(functions, n=5):
    print("\nPreview:")
    for fn in functions[:n]:
        print(f"  - {fn['full_name']} {fn['signature']}")
        print(f"    {fn['doc']}")
        print("    [has source]" if fn["source"] else "    [no source available]")
        print()


# build LLM prompt
def build_prompt(fn):
    prompt = f"""
You are a Python expert specializing in formal specifications.

Given the following function, infer its contract.

Function Name: {fn['name']}
Module: {fn['module']}
Signature: {fn['signature']}
Description: {fn['doc']}

STRICT RULES:
- Output ONLY valid JSON
- Do NOT include explanations
- Be precise and technical
- Preconditions = input requirements
- Postconditions = guarantees after execution
- Edge cases = unusual or boundary inputs

Return JSON:
{{
  "preconditions": [],
  "postconditions": [],
  "edge_cases": []
}}
"""
    return prompt.strip()


# main
if __name__ == "__main__":
    functions = collect_all_functions()

    print(f"\nTotal collected: {len(functions)}")

    save_functions(functions)
    preview(functions)

    print("\n--- SAMPLE PROMPT ---\n")
    print(build_prompt(functions[0]))