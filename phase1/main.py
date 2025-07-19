import os
import json
from pathlib import Path
from dotenv import load_dotenv
from tools.tools import (
    inspect_api_schema_tool,
    field_variation_mapper_tool,
    auth_requirement_checker_tool,
    rate_limit_detector_tool,
    missing_data_detector_tool,
    batching_and_retry_tool,
    api_documentation_generator_tool,
)

load_dotenv()

# ========== Setup ==========
Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("data/processed").mkdir(parents=True, exist_ok=True)
Path("data/logs").mkdir(parents=True, exist_ok=True)
Path("outputs").mkdir(parents=True, exist_ok=True)


def main():
    api_url = input("Enter API endpoint (e.g. https://...): ").strip()

    # === 1. Inspect API Schema ===
    print("[1] Inspecting schema...")
    schema = inspect_api_schema_tool.invoke(api_url)
    print("→ Fields discovered:", list(schema.keys())[:5])

    # === 2. Map Field Variations ===
    print("[2] Mapping field name variations...")
    fields = list(schema.keys()) if isinstance(schema, dict) else []
    field_mapping = field_variation_mapper_tool.invoke({"input": {"fields": fields}})


    # === 3. Check Auth Requirements ===
    print("[3] Checking authentication requirements...")
    auth_info = auth_requirement_checker_tool.invoke(api_url)

    # === 4. Detect Rate Limits ===
    print("[4] Checking rate limit headers...")
    rate_limits = rate_limit_detector_tool.invoke(api_url)

    # === 5. Check for Missing/Inconsistent Fields ===
    print("[5] Analyzing missing data...")
    missing_data = missing_data_detector_tool.invoke(api_url)

    # === 6. Intelligent Batching and Retry ===
    print("[6] Fetching full dataset in batches (3 pages)...")
    batch_result = batching_and_retry_tool.invoke(api_url)
    records = batch_result.get("records", [])

# === 7. Save Raw JSON Data ===
    print("[7] Saving raw data...")
    try:
        raw_path = "data/raw/raw_input.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        print(f"→ Raw dataset saved to: {raw_path}")
    except Exception as e:
        with open("data/logs/error.log", "a") as f:
            f.write(f"Raw data save failed: {str(e)}\n")

    # === 8. Generate Markdown Report ===
    print("[8] Generating structured Markdown report...")
    metadata = {
        "schema": schema,
        "field_mapping": field_mapping,
        "auth": auth_info,
        "rate_limits": rate_limits,
        "missing_data": missing_data,
        "batching_result": batch_result,
    }

    markdown = api_documentation_generator_tool.invoke({"metadata": metadata})

    output_path = "outputs/structured_api_report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f" Documentation saved to: {output_path}")


if __name__ == "__main__":
    main()
