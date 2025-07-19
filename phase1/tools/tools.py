from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Dict
import requests
import time
import json
from dotenv import load_dotenv

load_dotenv()

# === Field Variation Mapper Tool (LLM-based) ===
@tool
def field_variation_mapper_tool(input: Dict) -> Dict[str, str]:
    """
    Map raw field names to standardized names using the LLM.
    Expects input: { "fields": ["sqft", "zip", "sale_price"] }
    Returns a dictionary: { "sqft": "square_feet", ... }
    """
    try:
        fields = input.get("fields")
        if not isinstance(fields, list) or not all(isinstance(f, str) for f in fields):
            raise ValueError("Input must be a dict with a 'fields' key containing a list of strings.")

        llm = ChatOpenAI(model="gpt-4.1", temperature=0)
        prompt = (
            "You are a data analyst assistant. Given a list of raw API field names, map each one to its most likely standardized version.\n\n"
            f"Raw fields: {fields}\n\n"
            "Return ONLY a JSON dictionary where the keys are the original fields and values are the standardized names."
        )

        response = llm.invoke(prompt)

        try:
            result = json.loads(response)
            if isinstance(result, dict):
                return result
            else:
                return {"error": "Expected dictionary output from LLM.", "raw_output": response}
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response as JSON.", "raw_output": response}

    except Exception as e:
        return {"error": str(e)}


# === Inspect API Schema Tool ===
@tool
def inspect_api_schema_tool(api_url: str) -> Dict[str, str]:
    """Inspect an API endpoint and return field names with inferred data types."""
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        sample = data[0] if isinstance(data, list) and data else data
        schema = {k: type(v).__name__ for k, v in sample.items()}
        return schema
    except Exception as e:
        return {"error": str(e)}


# === Auth Requirement Checker ===
@tool
def auth_requirement_checker_tool(api_url: str) -> str:
    """Check if the API endpoint requires authentication."""
    try:
        r = requests.get(api_url, timeout=10)
        if r.status_code == 401:
            return "Authentication required (401)"
        return "No authentication required"
    except Exception:
        return "Could not determine"


# === Rate Limit Detector ===
@tool
def rate_limit_detector_tool(api_url: str) -> Dict[str, str]:
    """Detect if the API provides rate-limiting information in headers."""
    try:
        r = requests.get(api_url, timeout=10)
        return {
            "X-RateLimit-Limit": r.headers.get("X-RateLimit-Limit", "N/A"),
            "X-RateLimit-Remaining": r.headers.get("X-RateLimit-Remaining", "N/A"),
            "Retry-After": r.headers.get("Retry-After", "N/A"),
        }
    except Exception as e:
        return {"error": str(e)}


# === Missing Data Detector ===
@tool
def missing_data_detector_tool(api_url: str) -> Dict[str, float]:
    """Detect percentage of missing fields in the API response."""
    try:
        r = requests.get(api_url, timeout=10)
        r.raise_for_status()
        data = r.json()
        sample_data = data if isinstance(data, list) else [data]
        if not sample_data:
            return {"error": "No data available."}
        total = len(sample_data)
        keys = sample_data[0].keys()
        return {
            key: round(sum(1 for row in sample_data if not row.get(key)) / total * 100, 2)
            for key in keys
        }
    except Exception as e:
        return {"error": str(e)}


# === Batching and Retry Tool ===
@tool
def batching_and_retry_tool(api_url: str) -> dict:
    """
    Simulate paginated fetching (3 pages of 100) and retry on rate limit errors.
    Returns all records, a sample record, and metadata.
    """
    results = []
    for i in range(1, 4):  # Simulate 3 pages
        try:
            paged_url = f"{api_url}?$limit=100&$offset={(i - 1) * 100}"
            response = requests.get(paged_url, timeout=10)
            if response.status_code == 429:
                time.sleep(1)
                response = requests.get(paged_url)
            response.raise_for_status()
            data = response.json()
            results.extend(data if isinstance(data, list) else [data])
        except Exception as e:
            continue

    return {
        "records_fetched": len(results),
        "records": results,  # include all fetched records
        "sample_record": results[0] if results else {},
    }

# === Markdown Documentation Generator ===
@tool
def api_documentation_generator_tool(metadata: dict = {}) -> str:
    """Generate simple Markdown documentation from API metadata."""
    if not metadata:
        return "No metadata provided to document."

    lines = ["# API Documentation\n"]
    for key, value in metadata.items():
        lines.append(f"## {key}\n")
        lines.append("```json\n" + str(value) + "\n```\n")
    return "\n".join(lines)
