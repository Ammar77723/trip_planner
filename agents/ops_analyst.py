"""
Operations Analyst Agent
Monitors flights in a region, detects anomalies, and provides operational summaries.
"""
from crewai import Agent
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

from agents.mcp_tools import list_region_snapshot, list_active_alerts

# Initialize Groq LLM with minimal parameters
llm = ChatGroq(
    model="llama-3.1-8b-instant",  # Smaller, faster model
    temperature=0.3,  # Lower temperature for more focused responses
    max_tokens=500,  # Limit tokens to reduce costs
    groq_api_key=os.getenv("GROQ_API_KEY")
)


def create_ops_analyst_agent() -> Agent:
    """Create the Operations Analyst Agent"""
    
    return Agent(
        role="Airspace Operations Analyst",
        goal="Monitor flight traffic in assigned regions, identify anomalies, and provide clear operational summaries for airspace management",
        backstory="""You are an experienced airspace operations analyst with years of experience 
        monitoring flight traffic patterns. You excel at identifying unusual flight behaviors, 
        understanding airspace dynamics, and communicating critical information clearly to 
        operations teams.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[list_region_snapshot, list_active_alerts],
        max_iter=3,  # Limit iterations
        max_execution_time=30  # Timeout after 30 seconds
    )

