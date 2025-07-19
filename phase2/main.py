import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent

from tools.tools import (
    validate_required_fields,
    detect_outliers,
    log_errors_tool,
    filter_industrial_zoning,
)
from tools.utils import fetch_data

# Load environment variables
load_dotenv()

# === Compute Absolute Path to raw_input.json from Phase 1 ===
script_dir = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.path.normpath(os.path.join(script_dir, "..", "phase1", "data", "raw", "raw_input.json"))

if not os.path.exists(RAW_DATA_PATH):
    print(" Raw input file not found.")
    exit(1)

# === Load Raw Dataset ===
with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
    raw_data_str = f.read()
df = pd.read_json(raw_data_str)

# === LLM and Tool Setup ===
llm = ChatOpenAI(model="gpt-4.1", temperature=0)

tools = [
    Tool.from_function(validate_required_fields, name="ValidateRequiredFields", description="Validates required fields"),
    Tool.from_function(detect_outliers, name="DetectOutliers", description="Removes numerical outliers"),
    Tool.from_function(filter_industrial_zoning, name="FilterIndustrialZoning", description="Filters for industrial zoning"),
    Tool.from_function(log_errors_tool, name="LogErrors", description="Logs errors with context"),
]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a data cleaning assistant. Use the tools to clean property records step-by-step."),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, prompt=prompt, verbose=True)

# === Create Output Folders ===
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)

# === Batch Processing ===
batch_size = 50
results = []

for i, batch in enumerate(fetch_data(df, batch_size=batch_size), start=1):
    try:
        print(f"\n Processing batch {i}...")
        input_json = batch.to_dict(orient="records")

        instruction = (
            "Please clean this batch:\n"
            "1. Filter for industrial zoning properties\n"
            "2. Validate required fields\n"
            "3. Remove outliers\n"
            "Return clean JSON records."
        )

        result = agent_executor.invoke({"input": instruction + "\n" + json.dumps(input_json)})
        output = result.get("output")

        # ---  output handling ---
        if not output or not isinstance(output, str) or not output.strip().startswith("["):
            log_errors_tool.invoke(json.dumps({
                "batch": i,
                "llm_response": output,
                "error": "Output not valid JSON array"
            }))
            continue

        try:
            output_data = json.loads(output)
        except Exception as e:
            log_errors_tool.invoke(json.dumps({
                "batch": i,
                "llm_response": output,
                "error": f"JSON decode failed: {str(e)}"
            }))
            continue
        # --- output handling ---

        clean_batch = pd.DataFrame(output_data)
        results.append(clean_batch)

    except Exception as e:
        error_msg = json.dumps({"batch": i, "error": str(e)})
        log_errors_tool.invoke(error_msg)
        continue

# === Save Final Cleaned Dataset ===
if results:
    final_df = pd.concat(results, ignore_index=True)
    output_path = "data/processed/processed_data.csv"
    final_df.to_csv(output_path, index=False)
    print(f"\n Cleaned data saved to '{output_path}'")
else:
    print("\n No valid batches were processed.")
