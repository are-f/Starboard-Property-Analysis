from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import pandas as pd
from io import StringIO
import json
from dotenv import load_dotenv
import os

load_dotenv()
llm = ChatOpenAI(model="gpt-4.1", temperature=0)

def load_data_from_string(data_str: str) -> pd.DataFrame:
    try:
        parsed = json.loads(data_str)
        if isinstance(parsed, dict) and parsed.get("type") == "FeatureCollection":
            features = parsed.get("features", [])
            records = [f.get("properties", {}) for f in features]
            return pd.DataFrame(records)
        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
            return pd.DataFrame(parsed)
        raise ValueError("Unsupported JSON structure.")
    except json.JSONDecodeError:
        try:
            return pd.read_csv(StringIO(data_str))
        except Exception as e:
            raise ValueError("Unsupported format or malformed data.") from e

@tool
def validate_required_fields(df_data: str) -> str:
    """
    Validates required fields by letting LLM infer zoning, property type, and square footage columns
    from both column names and sample data rows.
    """
    try:
        df = load_data_from_string(df_data)
        if df.empty:
            return json.dumps([{"error": "Empty DataFrame"}])

        columns = list(df.columns)
        sample_rows = df[columns].head(3).to_dict(orient="records")
        prompt = (
            "Dataset sample rows:\n"
            f"{json.dumps(sample_rows, indent=2)}\n\n"
            "Based on both column names and the data, which column is most likely:\n"
            "- zoning or use code column (zoning codes look like M1, M2, I-1, etc.)\n"
            "- property type column\n"
            "- building square footage column\n"
            "Return JSON like: {\"zoning\": \"...\", \"property_type\": \"...\", \"square_feet\": \"...\"}.\n"
            "If you cannot identify, use null values."
        )

        response = llm.invoke(prompt)
        mapping = json.loads(response)

        zoning_col = mapping.get("zoning")
        type_col = mapping.get("property_type")
        sqft_col = mapping.get("square_feet")

        if not all([zoning_col, type_col, sqft_col]) or any(x is None for x in [zoning_col, type_col, sqft_col]):
            return json.dumps([{"error": "LLM failed to resolve all required columns."}])

        required = [zoning_col, type_col, sqft_col]
        df["missing_fields"] = df.apply(
            lambda row: [f for f in required if pd.isna(row.get(f)) or row.get(f) in ("", "NA", "")],
            axis=1
        )
        df_valid = df[df["missing_fields"].apply(lambda x: len(x) == 0)].drop(columns=["missing_fields"])

        return df_valid.to_json(orient="records")

    except Exception as e:
        return json.dumps([{"error": f"Field validation failed: {str(e)}"}])

@tool
def detect_outliers(data: str) -> str:
    """
    Removes numerical outliers using IQR filtering.
    Only processes numeric columns with more than one unique value.
    """
    try:
        df = load_data_from_string(data)
        if df.empty:
            return json.dumps([{"warning": "Empty dataset. No outliers to remove."}])

        numeric_cols = [col for col in df.select_dtypes(include="number").columns if df[col].nunique() > 1]
        if not numeric_cols:
            return json.dumps([{"warning": "No numeric columns with variance. Skipping outlier detection."}])

        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            df = df[(df[col] >= lower) & (df[col] <= upper)]

        return df.to_json(orient="records")

    except Exception as e:
        return json.dumps([{"error": f"Outlier detection failed: {str(e)}"}])

@tool
def filter_industrial_zoning(data: str) -> str:
    """
    Filters industrial properties using LLM to detect the zoning-related column,
    and matches against known industrial codes like M1, M2, I-1, 208, etc.
    """
    try:
        df = load_data_from_string(data)
        if df.empty:
            return json.dumps([])

        columns = list(df.columns)
        sample_rows = df[columns].head(3).to_dict(orient="records")
        prompt = (
            "You are identifying the zoning/use code column in tabular data.\n"
            "Here is a data sample:\n"
            f"{json.dumps(sample_rows, indent=2)}\n\n"
            "Which column holds the property zoning or land-use classification, such as M1, M2, I-1, I-2, 208, 209, etc.?\n"
            "Return the column name as a plain string. If you see none, reply null."
        )
        zoning_col = llm.invoke(prompt).strip().strip('"')
        if zoning_col == "null" or zoning_col not in df.columns:
            return json.dumps([{"error": f"LLM-guessed column '{zoning_col}' not found."}])

        df[zoning_col] = df[zoning_col].astype(str).str.upper().str.strip()
        industrial_codes = {"M1", "M2", "I-1", "I-2", "I1", "I2", "208", "209", "210", "211"}
        df = df[df[zoning_col].isin(industrial_codes)]
        return df.to_json(orient="records")

    except Exception as e:
        return json.dumps([{"error": f"Zoning filter failed: {str(e)}"}])

@tool
def log_errors_tool(error_context: str) -> str:
    """
    Logs error messages to console and to a log file.
    """
    try:
        print(f"[ERROR LOG]: {error_context}")
        log_dir = "data/logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "error_log.txt")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(error_context.strip() + "\n")
        return f"Logged: {error_context}"
    except Exception as e:
        return f"Logging failed: {str(e)}"
