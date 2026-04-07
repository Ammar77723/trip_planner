"""
CrewAI orchestration for the Airspace Copilot system.
Manages agent interactions and task execution.
"""
from crewai import Crew, Process, Task
from agents.ops_analyst import create_ops_analyst_agent
from agents.traveler_support import create_traveler_support_agent
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq LLM for crew (minimal parameters)
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3,
    max_tokens=400,
    groq_api_key=os.getenv("GROQ_API_KEY")
)


class AirspaceCopilotCrew:
    """Main crew orchestrating the airspace copilot agents"""
    
    def __init__(self):
        self.ops_analyst = create_ops_analyst_agent()
        self.traveler_support = create_traveler_support_agent()
    
    def analyze_region(self, region: str = "data") -> str:
        """
        Analyze a region for operational summary.
        
        Args:
            region: Region identifier
        
        Returns:
            Natural language summary of the region
        """
        task = Task(
            description=f"""Analyze the airspace region '{region}'. 
            Get the latest flight snapshot and check for any anomalies.
            Provide a clear, concise summary that includes:
            1. Total number of flights in the region
            2. Number of anomalies detected (if any)
            3. Brief description of any critical issues
            4. Overall airspace status
            
            Keep the summary under 200 words and use plain language.""",
            agent=self.ops_analyst,
            expected_output="A concise natural language summary of the region's flight status and any anomalies"
        )
        
        crew = Crew(
            agents=[self.ops_analyst],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
    
    def answer_traveler_question(self, question: str, callsign: str = None) -> str:
        """
        Answer a traveler's question about their flight.
        
        Args:
            question: User's question
            callsign: Optional flight callsign
        
        Returns:
            Natural language answer
        """
        # Extract callsign from question if not provided
        if not callsign:
            # Simple extraction - look for common flight ID patterns
            import re
            patterns = [
                r'\b([A-Z]{2,3}\d{1,4}[A-Z]?)\b',  # e.g., SWR7YT, THY4KZ
                r'\b([A-Z]{3}\d{4})\b',  # e.g., SIA217
            ]
            for pattern in patterns:
                match = re.search(pattern, question.upper())
                if match:
                    callsign = match.group(1)
                    break
        
        if not callsign:
            return "I need a flight callsign to help you. Please provide your flight number (e.g., SWR7YT, THY4KZ)."
        
        # Check if question needs ops analyst (e.g., asking about nearby flights with issues)
        needs_ops_analyst = any(keyword in question.lower() for keyword in [
            "nearby", "other flights", "issues", "problems", "anomalies", "region"
        ])
        
        if needs_ops_analyst:
            # Create task that uses A2A communication
            traveler_task = Task(
                description=f"""The traveler asked: "{question}"
                
                First, get information about flight {callsign} using the get_flight_by_callsign tool.
                Then, if the question is about nearby flights or regional issues, check active alerts.
                
                Provide a friendly, clear answer to the traveler's question. If there are any concerns 
                about nearby flights or the region, mention them but keep it reassuring.
                
                Keep your response under 150 words.""",
                agent=self.traveler_support,
                expected_output="A friendly, clear answer to the traveler's question"
            )
            
            crew = Crew(
                agents=[self.traveler_support, self.ops_analyst],
                tasks=[traveler_task],
                process=Process.sequential,
                verbose=True
            )
        else:
            # Simple traveler question
            traveler_task = Task(
                description=f"""The traveler asked: "{question}"
                
                Get information about flight {callsign} using the get_flight_by_callsign tool.
                Answer their question in a friendly, clear way using plain language.
                
                Keep your response under 150 words.""",
                agent=self.traveler_support,
                expected_output="A friendly, clear answer to the traveler's question"
            )
            
            crew = Crew(
                agents=[self.traveler_support],
                tasks=[traveler_task],
                process=Process.sequential,
                verbose=True
            )
        
        result = crew.kickoff()
        return str(result)

