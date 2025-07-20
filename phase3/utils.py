import pandas as pd
import json
from io import StringIO
from langchain_openai import ChatOpenAI

def load_data_from_file(filepath: str) -> pd.DataFrame:
    """Loads CSV, JSON, or GeoJSON as DataFrame."""
    if filepath.lower().endswith(".csv"):
        return pd.read_csv(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("type") == "FeatureCollection":
            features = data.get("features", [])
            records = [feat.get("properties", {}) for feat in features if "properties" in feat]
            return pd.DataFrame(records)
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            return pd.DataFrame.from_dict(data)
    except Exception:   
        pass
    try:
        return pd.read_csv(StringIO(text))
    except Exception:
        raise ValueError(f"Could not parse file '{filepath}' as CSV, JSON, or GeoJSON.")

def get_llm_text_response(response):
    if hasattr(response, "content"):
        return response.content
    else:
        return str(response)

def infer_column_mapping(df):
    llm = ChatOpenAI(model="gpt-4.1", temperature=0)
    sample = df.head(5).to_dict(orient="records")
    columns = list(df.columns)
    prompt = (
        "These are the columns in a real estate dataset:\n"
        f"{columns}\n\n"
        "Here are a few sample rows:\n"
        f"{json.dumps(sample, indent=2)}\n\n"
        "Which columns best match the following logical fields (return as JSON, use null if missing):\n"
        '{"property_type": , "size": , "age": , "address": }\n'
        "property_type = column for type or use (e.g., industrial, office, etc)\n"
        "size = building size in square feet.\n"
        "age = property age or year built column\n"
        "address = a field with an address or property description."
    )
    response = llm.invoke(prompt)
    response_text = get_llm_text_response(response).strip()
    
    # --- ROBUST CODE FENCE REMOVAL ---
    # Remove `````` from start
    if response_text.startswith("```"):
        # Find the first newline after ```
        first_newline = response_text.find('\n')
        if first_newline != -1:
            response_text = response_text[first_newline + 1:]
    
    # Remove ```
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()
    
    # --- END ROBUST REMOVAL ---
    
    try:
        mapping = json.loads(response_text)
        for k in ["property_type", "size", "age", "address"]:
            if k not in mapping:
                mapping[k] = None
        return mapping
    except Exception:
        raise ValueError(f"LLM failed to extract mapping. Got: {response_text}")


def geo_distance_km(coord1, coord2):
    from geopy.distance import geodesic
    try:
        return geodesic(coord1, coord2).km
    except Exception:
        return float('nan')
