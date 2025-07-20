# Starboard Property Analysis System
 A comprehensive AI-powered property data analysis system that discovers APIs, cleans property data, and finds comparable properties using intelligent agents.

# Project Overview
 This project is organized into three phases, each handling a specific aspect of property data analysis:
- Phase 1: API Discovery and Data Ingestion
- Phase 2: Data Cleaning and Validation
- Phase 3: Comparable Property Discovery



# Phase-by-Phase Guide
## Phase 1: API Discovery and Data Ingestion
### Purpose
Automatically discovers, catalogs, and ingests property data from various APIs with intelligent field mapping and authentication handling.

### Features
- API Discovery: Automatically detects and catalogs available APIs

- Field Mapping: Maps data fields across different API schemas

- Authentication: Handles API keys, rate limits, and authentication requirements

- Format Support: Handles JSON, CSV, and GeoJSON responses

- Data Validation: Identifies missing or inconsistent data types


## Phase 2: Data Cleaning and Validation
### Purpose
 Processes raw property data with intelligent filtering, validation, and outlier detection specifically focused on industrial properties.

### Features
- Industrial Zoning Filter: Automatically detects and filters for industrial zoning codes (M1, M2, I-1, I-2, 5-*, etc.)

- Schema-Agnostic Processing: Uses LLM to understand different data schemas

- Required Field Validation: Ensures presence of property type, zoning, and size fields

- Outlier Detection: Removes statistical outliers using IQR method

- Error Logging: Comprehensive error logging to files and console

- Batch Processing: Handles large datasets efficiently

### Key Components
- Tools (phase2/tools/tools.py)
- validate_required_fields(): LLM-powered field validation

- filter_industrial_zoning(): Intelligent zoning code detection

- detect_outliers(): IQR-based outlier removal

- log_errors_tool(): Error logging with file output

### Usage

#### Ensure Phase 1 output exists at phase1/data/raw/raw_input.json
python phase2/main.py
- Input/Output
- Input: phase1/data/raw/raw_input.json

- Output: data/processed/processed_data.csv

- Logs: data/logs/error_log.txt

### Processing Workflow
1. Load raw data from Phase 1

2. Process in batches (configurable batch size)

3. For each batch:

4. Filter for industrial zoning properties

5. Validate required fields are present

6. Remove statistical outliers

7. Save cleaned data to processed directory

## Phase 3: Comparable Property Discovery
### Purpose
- Finds similar properties using advanced similarity scoring based on size, location, age, and property type with LLM-powered explanations.

### Features
- Multi-Format Support: Accepts CSV, JSON, or GeoJSON input files

- Schema-Agnostic: Automatically detects relevant columns using LLM

- Interactive Selection: User-friendly property selection interface

- Similarity Scoring: Weighted similarity calculation based on:

1. Property type (35%)

2. Location proximity (35%)

3. Building size (20%)

4. Property age (10%)

- LLM Explanations: Human-readable explanations for each comparable

- Flexible Input: Command-line arguments and interactive modes

### Key Components
#### phase3/agent.py
1.  Main entry point with interactive CLI

2. Property selection interface

3. Results display and explanation generation

#### phase3/comparables.py
1. Core similarity calculation algorithms

2. Comparable property finding logic

3. Scoring and ranking functions

#### phase3/utils.py
1. Universal data loading (CSV/JSON/GeoJSON)

2. LLM-powered column mapping

3. Geographic distance calculations



## Example Output

- === SELECTED SUBJECT PROPERTY === 

-Type: Industrial Warehouse

- Address: 123 Industrial Blvd
- Size: 50000 sqft
- Age: 15 years

=== TOP 5 COMPARABLE PROPERTIES ===

1. Score: 0.887
   - Type: Industrial Warehouse  
   - Address: 456 Manufacturing St
   - Size: 48000 sqft
   - Explanation: This is an excellent comparable due to identical property type (industrial warehouse), very similar size (48,000 vs 50,000 sqft - only 4% difference), and close proximity in the same industrial district.
#### Configuration
- Similarity Weights
Default weights in phase3/agent.py:

- WEIGHTS = {
    "type": 0.35,        
    "location": 0.35,     
    "size": 0.20,        
    "age": 0.10          
}
#### Batch Processing
Default batch size in phase2/main.py:

- batch_size = 50 
 Adjust based on memory and API limits
### LLM Integration
- The system uses OpenAI GPT-4 for:

- Schema Understanding: Automatically mapping column names to logical fields

- Industrial Code Detection: Identifying zoning codes across different jurisdictions

- Comparable Explanations: Generating human-readable explanations for matches

## Data Support
Input Formats
CSV: Standard comma-separated values

JSON: Array of objects or single object with arrays

GeoJSON: FeatureCollection with properties

## Common Data Sources
- Cook County Assessor Data: https://datacatalog.cookcountyil.gov/resource/ijzp-q8t2.json

- Dallas County CAD: Property assessment data

- Los Angeles County: GIS property data

## Example Workflows
Complete Pipeline
bash
- Phase 1: Discover and ingest API data
python phase1/main.py

- Phase 2: Clean and validate data
python phase2/main.py

- Phase 3: Find comparables interactively
python -m phase3.agent
Direct Phase 3 Usage

## Troubleshooting
Common Issues

- JSON decode errors

- LLM responses with code blocks are automatically handled

- Check API key configuration if LLM calls fail

- Empty processed data

- Verify industrial properties exist in your dataset

- Check error logs in data/logs/error_log.txt

- No comparables found

- Dataset may not contain properties similar to subject

- Try adjusting similarity weights

- Use larger dataset

## Error Logging
All errors are logged to:

- data/logs/error_log.txt (automatically created)

## Contributing
- Each phase is modular and can be extended independently

- Add new similarity metrics in phase3/comparables.py

- Extend data source support in respective phase utils

- Add new cleaning tools in phase2/tools/tools.py