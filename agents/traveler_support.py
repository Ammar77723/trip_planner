"""
Traveler Support Agent
Answers user questions about specific flights using natural language.
"""
from crewai import Agent
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

from agents.mcp_tools import get_flight_by_callsign, list_active_alerts

# Initialize Groq LLM with minimal parameters
llm = ChatGroq(
    model="llama-3.1-8b-instant",  # Smaller, faster model
    temperature=0.5,  # Slightly higher for more natural conversation
    max_tokens=300,  # Limit tokens for chat responses
    groq_api_key=os.getenv("GROQ_API_KEY")
)


def create_traveler_support_agent() -> Agent:
    """Create the Traveler Support Agent"""
    
    return Agent(
        role="Personal Flight Watchdog Assistant",
        goal="Help travelers track their flights, answer questions about flight status, and provide clear, friendly explanations about flight information",
        backstory="""You are a helpful and friendly flight tracking assistant. You help travelers 
        understand where their flights are, what their flight status means, and answer questions 
        in plain, easy-to-understand language. You're patient, clear, and always try to be helpful.""",
        verbose=True,
        allow_delegation=True,  # Can delegate to ops analyst if needed
        llm=llm,
        tools=[get_flight_by_callsign, list_active_alerts],
        max_iter=3,  # Limit iterations
        max_execution_time=30  # Timeout after 30 seconds
    )

