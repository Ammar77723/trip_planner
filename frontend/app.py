"""
Streamlit frontend for the Airspace Copilot system.
Provides UI for both Traveler Mode and Operations Mode.
"""
import streamlit as st
import requests
import json
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8001"

st.set_page_config(
    page_title="Airspace Copilot",
    page_icon="✈️",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .mode-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">✈️ Airspace Copilot</h1>', unsafe_allow_html=True)

# Sidebar for mode selection
st.sidebar.title("Navigation")
mode = st.sidebar.radio(
    "Select Mode",
    ["Traveler Mode", "Operations Mode"],
    index=0
)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if mode == "Traveler Mode":
    st.markdown('<h2 class="mode-header">👤 Personal Flight Watchdog</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Track Your Flight")
        flight_input = st.text_input(
            "Enter Flight Callsign or ICAO24",
            placeholder="e.g., SWR7YT, THY4KZ, or 4baa1a",
            key="flight_input"
        )
        
        st.subheader("💬 Chat with Flight Assistant")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for i, (role, message) in enumerate(st.session_state.chat_history):
                if role == "user":
                    st.markdown(f"**You:** {message}")
                else:
                    st.markdown(f"**Assistant:** {message}")
                st.markdown("---")
        
        # Chat input
        user_question = st.text_input(
            "Ask a question about your flight",
            placeholder="e.g., Where is my flight now? Is it climbing or descending?",
            key="chat_input"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Send Question", type="primary"):
                if user_question and flight_input:
                    with st.spinner("Getting flight information..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/api/answer-question",
                                json={
                                    "question": user_question,
                                    "callsign": flight_input.upper().strip()
                                },
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                answer = data.get("answer", "No answer received")
                                
                                # Add to chat history
                                st.session_state.chat_history.append(("user", user_question))
                                st.session_state.chat_history.append(("assistant", answer))
                                
                                st.rerun()
                            else:
                                st.error(f"Error: {response.text}")
                        except Exception as e:
                            st.error(f"Error connecting to API: {str(e)}")
                else:
                    st.warning("Please enter both a flight callsign and a question.")
        
        with col_btn2:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    with col2:
        st.subheader("Quick Actions")
        if st.button("Where is my flight?"):
            if flight_input:
                st.session_state.chat_history.append(("user", "Where is my flight now?"))
                # Trigger API call
                with st.spinner("Getting location..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/answer-question",
                            json={
                                "question": "Where is my flight now?",
                                "callsign": flight_input.upper().strip()
                            },
                            timeout=60
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.chat_history.append(("assistant", data.get("answer", "")))
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Enter a flight callsign first")
        
        if st.button("Is my flight climbing?"):
            if flight_input:
                st.session_state.chat_history.append(("user", "Is my flight climbing or descending?"))
                with st.spinner("Checking..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/answer-question",
                            json={
                                "question": "Is my flight climbing or descending?",
                                "callsign": flight_input.upper().strip()
                            },
                            timeout=60
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.chat_history.append(("assistant", data.get("answer", "")))
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Enter a flight callsign first")

else:  # Operations Mode
    st.markdown('<h2 class="mode-header">🛫 Airspace Operations Copilot</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Region Selection")
        region = st.selectbox(
            "Select Region",
            ["data", "region1", "region2"],
            index=0,
            help="Choose the region to analyze"
        )
        
        if st.button("Analyze Region", type="primary"):
            with st.spinner("Analyzing region... This may take a moment."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/analyze-region",
                        json={"region": region},
                        timeout=90
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["ops_summary"] = data.get("summary", "")
                        st.session_state["ops_region"] = region
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")
    
    with col2:
        st.subheader("Operational Summary")
        if "ops_summary" in st.session_state:
            st.info(f"**Region:** {st.session_state.get('ops_region', 'N/A')}")
            st.markdown("---")
            st.markdown(st.session_state["ops_summary"])
        else:
            st.info("Select a region and click 'Analyze Region' to get a summary")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #7f7f7f;'>"
    "Airspace Copilot System | Powered by CrewAI & Groq LLM"
    "</div>",
    unsafe_allow_html=True
)

