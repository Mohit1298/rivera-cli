# Rivera + LangGraph Integrations

This directory contains several out-of-the-box examples demonstrating how to integrate Rivera's persistent memory capabilities into LangGraph agents.

All examples share the core Rivera tools defined in core/rivera_tools.py (except rivera_base_store which implements a native LangGraph BaseStore).

## Directory Setup

`bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Rivera and LLM API keys
`

## Running the Examples

Because the examples share the core tools module, you should run them as Python modules from this root directory:

`bash
python -m basic_integration.demo
python -m cross_session_recall.main
python -m custom_memory_saver.run_demo
python -m research_pipeline.run_full_pipeline

# For the advanced BaseStore implementation (PR 571):
python -m rivera_base_store.run_full_demo
# Or run its Streamlit UI:
streamlit run rivera_base_store/app.py
`

## Available Examples

* **[`rivera_base_store/`](./rivera_base_store/README.md)**: (NEW) A robust customer-support agent using a native `RiveraStore(BaseStore)` implementation for cross-session recall. Includes a Streamlit UI, contradiction resolution logic, and a **detailed architectural README**.
* **basic_integration/**: A minimal, drop-in example of using Rivera tools within a simple LangGraph agent.
* **cross_session_recall/**: An agent designed to remember facts and preferences across different conversation sessions.
* **research_pipeline/**: A multi-agent setup where one agent researches and saves facts to Rivera, and another synthesizes them.
* **custom_memory_saver/**: An advanced implementation showing how to integrate Rivera directly at the LangGraph CheckpointSaver level.
