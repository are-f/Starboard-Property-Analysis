# agent.py

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.agents import Tool

from tools.tools import (
    validate_required_fields,
    detect_outliers,
    filter_industrial_zoning,
    log_errors_tool,
)

# Load environment variables (e.g., OpenAI key)
load_dotenv()

# === Language Model ===
llm = ChatOpenAI(model="gpt-4.1", temperature=0)

# === Tool Wrapping ===
tools = [
    Tool.from_function(
        func=filter_industrial_zoning,
        name="FilterIndustrialZoning",
        description="Filters dataset for industrial zoning codes (M1, M2, I-1, I-2, etc.)"
    ),
    Tool.from_function(
        func=validate_required_fields,
        name="ValidateRequiredFields",
        description="Validates presence of required fields: property_type, zoning_classification, square_feet"
    ),
    Tool.from_function(
        func=detect_outliers,
        name="DetectOutliers",
        description="Removes outliers in numeric fields using the IQR method"
    ),
    Tool.from_function(
        func=log_errors_tool,
        name="LogErrors",
        description="Logs processing or validation errors with context"
    ),
]

# === Prompt Template ===
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a property data cleaning and validation agent. "
     "Use the tools to filter industrial records, validate required fields, detect outliers, "
     "and log errors with context. Respond with the cleaned dataset as JSON."),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# === Create Agent ===
agent = create_openai_functions_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# === Agent Executor ===
data_agent = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)
