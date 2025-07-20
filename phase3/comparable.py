import pandas as pd
import numpy as np
from utils import geo_distance_km

def type_similarity(type1, type2):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, str(type1 or "").lower(), str(type2 or "").lower()).ratio()

def size_similarity(size1, size2):
    try:
        size1, size2 = float(size1), float(size2)
        pct_diff = abs(size1 - size2) / max(size1, 1)
        return max(0, 1 - pct_diff)
    except Exception:
        return 0.0

def age_similarity(age1, age2):
    try:
        age1, age2 = float(age1), float(age2)
        diff = abs(age1 - age2)
        return max(0, 1 - (diff / max(age1, 1)))
    except Exception:
        return 0.0

def location_similarity(lat1, lon1, lat2, lon2, loc_scale_km=2.5):
    try:
        d = geo_distance_km((lat1, lon1), (lat2, lon2))
        if np.isnan(d):
            return 0.0
        return np.exp(-d / loc_scale_km)
    except Exception:
        return 0.0

def get_subject_dict(df: pd.DataFrame, selection_criteria: dict, mapping: dict) -> dict:
    # Example: select by unique ID or just first record.
    return df.iloc[0].to_dict()

def compute_similarity(subject: dict, candidate: dict, mapping: dict, weights: dict) -> float:
    t_sim = type_similarity(subject.get(mapping["property_type"]), candidate.get(mapping["property_type"]))
    sz_sim = size_similarity(subject.get(mapping["size"]), candidate.get(mapping["size"]))
    ag_sim = age_similarity(subject.get(mapping["age"]), candidate.get(mapping["age"]))
    lat1, lon1, lat2, lon2 = subject.get("latitude"), subject.get("longitude"), candidate.get("latitude"), candidate.get("longitude")
    loc_sim = location_similarity(lat1, lon1, lat2, lon2) if lat1 and lon1 and lat2 and lon2 else 0.0
    score = (weights['type']*t_sim + weights['location']*loc_sim + weights['size']*sz_sim + weights['age']*ag_sim)
    return round(score, 4)

def find_comparables(subject: dict, db: pd.DataFrame, mapping: dict, weights=None, top_n=5) -> list:
    if weights is None:
        weights = {'type':0.35, 'location':0.35, 'size':0.2, 'age':0.1}
    comparables = []
    for _, row in db.iterrows():
        candidate = row.to_dict()
        score = compute_similarity(subject, candidate, mapping, weights)
        candidate['comparable_score'] = score
        comparables.append(candidate)
    comparables.sort(key=lambda c: c['comparable_score'], reverse=True)
    return comparables[:top_n]
