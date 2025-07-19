# Overview
The API Discovery Agent is an intelligent system built using LangChain and tool-based modular design. It automatically:
- Discovers and catalogs APIs from public data portals

- Extracts available fields and schema definitions

- Maps field name variations to standardized names

- Identifies required authentication and rate-limiting rules

- Detects missing or inconsistent data types

- Applies intelligent batching and retry mechanisms

- Outputs clean Markdown-based documentation

# This agent is designed to work with municipal and county-level open data APIs, of:
- Cook County: https://datacatalog.cookcountyil.gov/

# Agent Capabilities
- API Schema Inspection:	Auto-detects data fields and infers types
- Auth Detection:	Checks if API requires authentication
- Rate Limit Awareness:	Detects and respects rate limits
- Retry & Batching:	Implements offset-based paging and auto-retry
- Field Normalization:	Maps variations like sqft, square_feet, building_area
- Missing Data Analysis:	Detects nulls, missing fields, and inconsistencies
- Auto-Documentation:	Generates markdown documentation from metadata
# Technologies Used
- Python 
- LangChain 
- OpenAI API (or any LLM via LangChain)
- Pydantic + Requests
- Markdown/JSON I/O

# Some of the sample input APIs are as follows:
- https://datacatalog.cookcountyil.gov/resource/3r7i-mrz4.json
- https://datacatalog.cookcountyil.gov/resource/y282-6ig3.json
- https://datacatalog.cookcountyil.gov/resource/uzyt-m557.json

