import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# Validate API keys
if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY")

if not HF_API_KEY:
    raise ValueError("Missing HF_API_KEY")

# Model configs
GROQ_MODEL = "llama-3.3-70b-versatile"
HF_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"


# Utility: safe response extraction
def extract_content(response_data):
    try:
        return response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ValueError(f"Invalid API response format: {response_data}")


# GROQ API
def generate_with_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)

    if response.status_code != 200:
        print(f"[GROQ ERROR] {response.status_code}")
        print(response.text)
        raise RuntimeError("Groq API request failed")

    response_data = response.json()
    return extract_content(response_data)


# Hugging Face API
def generate_with_hf(prompt):
    url = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": HF_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 500
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)

    if response.status_code != 200:
        print(f"[HF ERROR] {response.status_code}")
        print(response.text)
        raise RuntimeError("Hugging Face API request failed")

    response_data = response.json()
    return extract_content(response_data)


# Main function
if __name__ == "__main__":
    test_function = """
def remove_duplicates(lst):
    return list(set(lst))
"""

    prompt = f"""
You are given a Python function. Extract its contract.

Return ONLY this JSON structure, no explanation, no markdown:
{{
  "preconditions": [],
  "postconditions": [],
  "edge_cases": []
}}

Function:
{test_function}
"""

    print("Calling Groq...")
    groq_result = generate_with_groq(prompt)

    print("Calling Hugging Face...")
    hf_result = generate_with_hf(prompt)

    print("\n=== GROQ (Llama-3.3 70B) OUTPUT ===")
    print(groq_result)

    print("\n=== HUGGING FACE (Llama-3 8B) OUTPUT ===")
    print(hf_result)