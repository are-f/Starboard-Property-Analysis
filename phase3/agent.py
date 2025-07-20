from utils import load_data_from_file, infer_column_mapping
from comparable import find_comparables, get_subject_dict
from prompt_template import comparable_explanation_prompt
from langchain_openai import ChatOpenAI
import pandas as pd 
from dotenv import load_dotenv
load_dotenv()

WEIGHTS = {"type":0.35, "location":0.35, "size":0.2, "age":0.1}

#The path is of raw_input, but after debugging, this should be the path of processed data which shall reside in "data/processed/".
DEFAULT_PATH = "C:/Users/devra/Desktop/starboard_ai - Copy/Starboard-Property-Analysis/phase1/data/raw/raw_input.json" #Change this path as required.


def display_property_options(df, mapping, limit=10):
    """Show first N properties for user to choose from"""
    print(f"\n=== Available Properties (showing first {limit}) ===")
    for idx, row in df.head(limit).iterrows():
        prop_type = row.get(mapping['property_type'], 'N/A')
        address = row.get(mapping['address'], 'N/A')
        size = row.get(mapping['size'], 'N/A')
        print(f"{idx}. {prop_type} | {address} | {size} sqft")
    print(f"{limit}. [Enter custom row index]")
    print(f"{limit+1}. [Search by address/name]")

def get_user_property_selection(df, mapping):
    """Interactive property selection"""
    while True:
        display_property_options(df, mapping)
        try:
            choice = input(f"\nSelect property (0-{len(df)-1}) or option: ").strip()
            
            if choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(df):
                    return df.iloc[idx].to_dict()
                elif idx == 10:  # Custom index
                    custom_idx = int(input(f"Enter row index (0-{len(df)-1}): "))
                    if 0 <= custom_idx < len(df):
                        return df.iloc[custom_idx].to_dict()
                elif idx == 11:  # Search by address
                    search_term = input("Enter address/property name to search: ").lower()
                    address_col = mapping['address']
                    if address_col:
                        matches = df[df[address_col].str.lower().str.contains(search_term, na=False)]
                        if not matches.empty:
                            print(f"\nFound {len(matches)} matches:")
                            for idx, row in matches.head(5).iterrows():
                                print(f"{idx}. {row.get(address_col)} | {row.get(mapping['property_type'])}")
                            match_idx = int(input("Select match by index: "))
                            return df.iloc[match_idx].to_dict()
                        else:
                            print("No matches found.")
                            continue
            else:
                print("Invalid input. Please try again.")
        except (ValueError, IndexError):
            print("Invalid selection. Please try again.")

def run_comparables(filepath=None, subject_criteria=None, top_n=5, explain=True, interactive=True):
    filepath = filepath or DEFAULT_PATH
    df = load_data_from_file(filepath)

    mapping = infer_column_mapping(df)
    print(f"Column mapping detected: {mapping}")

    # Handle numeric conversions
    for k in ["size", "age"]:
        col = mapping.get(k)
        if col and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Handle year-built as age
    if mapping.get("age") and "year" in mapping.get("age", "").lower():
        df["__computed_age"] = 2024 - pd.to_numeric(df[mapping["age"]], errors="coerce")
        mapping["age"] = "__computed_age"

    # Interactive vs programmatic selection
    if interactive and not subject_criteria:
        subject = get_user_property_selection(df, mapping)
    else:
        subject = get_subject_dict(df, subject_criteria or {}, mapping)

    print(f"\n=== SELECTED SUBJECT PROPERTY ===")
    print(f"Type: {subject.get(mapping['property_type'], 'N/A')}")
    print(f"Address: {subject.get(mapping['address'], 'N/A')}")
    print(f"Size: {subject.get(mapping['size'], 'N/A')} sqft")
    print(f"Age: {subject.get(mapping['age'], 'N/A')} years")

    comps = find_comparables(subject, df, mapping, WEIGHTS, top_n=top_n)
    
    print(f"\n=== TOP {top_n} COMPARABLE PROPERTIES ===")
    for idx, comp in enumerate(comps, 1):
        print(f"\n{idx}. Score: {comp['comparable_score']:.3f}")
        print(f"   Type: {comp.get(mapping['property_type'],'N/A')}")
        print(f"   Address: {comp.get(mapping['address'],'N/A')}")
        print(f"   Size: {comp.get(mapping['size'],'N/A')} sqft")
        
        if explain:
            llm = ChatOpenAI(model="gpt-4.1", temperature=0)
            subj_dict = {k: subject.get(k) for k in mapping.values() if k}
            comp_dict = {k: comp.get(k) for k in mapping.values() if k}
            prompt = comparable_explanation_prompt(str(subj_dict), str(comp_dict))
            explanation = llm.invoke(prompt)
            explanation = explanation.content if hasattr(explanation, "content") else explanation
            print(f"   Explanation: {explanation.strip()}")
    
    return comps

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Find comparable properties")
    parser.add_argument("filepath", nargs="?", help="Path to property data file")
    parser.add_argument("--top-n", type=int, default=5, help="Number of comparables to return")
    parser.add_argument("--no-interactive", action="store_true", help="Skip interactive selection")
    parser.add_argument("--no-explain", action="store_true", help="Skip LLM explanations")
    
    args = parser.parse_args()
    
    run_comparables(
        filepath=args.filepath,
        top_n=args.top_n,
        explain=not args.no_explain,
        interactive=not args.no_interactive
    )
