# utils.py

import pandas as pd
import json
from io import StringIO
import requests

def load_data_from_string(data_str: str) -> pd.DataFrame:
    """
    Load data from JSON, CSV, or GeoJSON string.
    Supports:
    - JSON list of dicts
    - GeoJSON FeatureCollection
    - CSV string
    """
    try:
        parsed = json.loads(data_str)

        # GeoJSON
        if isinstance(parsed, dict) and parsed.get("type") == "FeatureCollection":
            features = parsed.get("features", [])
            records = [f.get("properties", {}) for f in features]
            return pd.DataFrame(records)

        # JSON array of objects
        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
            return pd.DataFrame(parsed)

        raise ValueError("Unsupported JSON structure.")
    except json.JSONDecodeError:
        try:
            return pd.read_csv(StringIO(data_str))
        except Exception as e:
            raise ValueError("Unsupported format or malformed data") from e


def fetch_data(df: pd.DataFrame, batch_size: int = 50):
    """
    Yields DataFrame batches.
    """
    for i in range(0, len(df), batch_size):
        yield df.iloc[i:i + batch_size]


def fetch_dataset_from_api(url: str) -> pd.DataFrame:
    """
    Calls external API and returns DataFrame using universal loader.
    Used in Phase 1 only.
    """
    response = requests.get(url)
    response.raise_for_status()
    return load_data_from_string(response.text)
