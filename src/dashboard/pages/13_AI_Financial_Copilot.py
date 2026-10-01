"""Screen 13: Interactive AI Financial Research Copilot."""
import os
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath("."))
from src.nlp.copilot_engine import copilot

st.set_page_config(page_title="AI Financial Copilot - Nifty 100", page_icon="💬", layout="wide")

st.title("💬 AI Financial Research Copilot")
st.markdown("""
**Natural Language Equity Research Assistant**: Ask complex financial, forensic, valuation, or screening questions in plain English across the 92 Nifty 100 companies. Powered by multi-layer intent parsing, database query synthesis, and forensic triangulation.
""")

# Initialize chat history in session state
if "copilot_messages" not in st.session_state:
    st.session_state.copilot_messages = [
        {
            "role": "assistant",
            "content": """👋 **Hello! I am your Nifty 100 AI Financial Copilot.**

I can instantly analyze companies, evaluate forensic accounting risks, compare peer competitors, scan for machine learning anomalies, or explain complex valuation models.

**Try asking or clicking one of the sample prompts below!**"""
        }
    ]

# Sidebar with quick prompt chips & controls
st.sidebar.header("💡 Prompt Starters")
st.sidebar.markdown("Click any preset query to execute instantly:")

prompt_options = [
    ("🔍 Analyze Tata Motors", "Analyze Tata Motors"),
    ("⚖️ Compare TCS vs Infosys", "Compare TCS and Infosys"),
    ("⚠️ Top Forensic Red Flags", "Which companies have high Beneish M-score?"),
    ("🤖 ML Accounting Anomalies", "Show me the top ML anomalies"),
    ("🎯 Zero Debt Leaders", "Find zero debt companies"),
    ("🚨 Bankruptcy Distress Zone", "Show distress zone companies"),
    ("📖 What is Beneish M-Score?", "What is Beneish M-score?"),
    ("📈 How Monte Carlo DCF Works", "How does Monte Carlo DCF work?")
]

preset_clicked = None
for label, query_text in prompt_options:
    if st.sidebar.button(label, use_container_width=True):
        preset_clicked = query_text

if st.sidebar.button("🗑️ Clear Conversation", type="secondary", use_container_width=True):
    st.session_state.copilot_messages = [
        {
            "role": "assistant",
            "content": "Conversation reset. How can I assist your equity research today?"
        }
    ]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("""
**Copilot Capabilities:**
• **Single Stock Deep-Dives**: Comprehensive fundamentals, health score, and forensic audit.  
• **Head-to-Head Comparisons**: Side-by-side metrics with winner advantages.  
• **Forensic & Distress Triage**: Beneish M, Altman Z, and Piotroski F.  
• **Machine Learning Outliers**: Isolation Forest anomaly rankings.  
• **Custom Screening**: Filter by sector, leverage, and ROE.
""")

# Render existing chat conversation
for msg in st.session_state.copilot_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input via chat input box or preset button
user_prompt = st.chat_input("Ask a question (e.g. 'Analyze Reliance', 'Compare HDFC Bank and ICICI Bank', 'Find high ROE tech stocks')...")

# If a preset button was clicked, treat it as the user prompt
if preset_clicked:
    user_prompt = preset_clicked

if user_prompt:
    # Append user message
    st.session_state.copilot_messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing financial filings, forensic models & ML scores..."):
            response_text = copilot.ask(user_prompt)
            st.markdown(response_text)

    # Append assistant message to state
    st.session_state.copilot_messages.append({"role": "assistant", "content": response_text})
