from langchain.agents import initialize_agent, AgentType
from langchain.agents.tools import Tool
from langchain_openai import ChatOpenAI

# Import tools from your tool file
from tools.tools import (
    discover_api_endpoints_tool,
    inspect_api_schema_tool,
    field_variation_mapper_tool,
    auth_requirement_checker_tool,
    rate_limit_detector_tool,
    missing_data_detector_tool,
    batching_and_retry_tool,
    api_documentation_generator_tool,
    field_variation_mapper_tool
)

# Define tool wrappers
tools = [
    Tool.from_function(discover_api_endpoints_tool),
    Tool.from_function(inspect_api_schema_tool),
    Tool.from_function(field_variation_mapper_tool),
    Tool.from_function(auth_requirement_checker_tool),
    Tool.from_function(rate_limit_detector_tool),
    Tool.from_function(missing_data_detector_tool),
    Tool.from_function(batching_and_retry_tool),
    Tool.from_function(api_documentation_generator_tool),
    Tool.from_function(field_variation_mapper_tool)
]

# LLM model (adjust temperature as needed)
llm = ChatOpenAI(temperature=0, model="gpt-4.1")  

# Initialize Agent
api_discovery_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    handle_parsing_errors=True
)
