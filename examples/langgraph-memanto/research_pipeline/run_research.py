"""
Run 1: Research Agent stores findings in Rivera via LangGraph.

This script proves that memories persist across sessions.
Run this script, then run run_writer.py in a new terminal --
the writer will retrieve the SAME memories from Rivera.
"""

from __future__ import annotations

import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from research_pipeline.pipeline.graph import run_research

load_dotenv()

RIVERA_API_KEY = os.getenv("RIVERA_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
AGENT_ID = os.getenv("RIVERA_AGENT_ID", "langgraph-research-team")
TOPIC = os.getenv("RESEARCH_TOPIC", "AI agent framework market size and trends 2024")


def main():
    if not RIVERA_API_KEY or not OPENROUTER_API_KEY:
        print("ERROR: Missing API keys.")
        print(
            "Copy .env.example to .env and fill in RIVERA_API_KEY and OPENROUTER_API_KEY"
        )
        sys.exit(1)

    print(f"Research Agent analyzing: {TOPIC}")
    print(f"Rivera Agent ID: {AGENT_ID}")
    print("---")

    # Uses the compiled LangGraph which binds rivera_remember as a tool
    # and actually invokes it via tool calls (not plain-text instructions)
    result = run_research(topic=TOPIC, rivera_agent_id=AGENT_ID)

    print("\n[Research Agent Complete]")
    print(f"Total messages: {len(result.get('messages', []))}")
    print(f"Findings stored: {len(result.get('findings', []))}")

    for msg in result.get("messages", []):
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if content:
            print(f"\n[{role.upper()}]\n{content[:500]}")

    print(f"\nMemories stored in Rivera (agent_id={AGENT_ID})")
    print("Run run_writer.py in a new terminal to retrieve them!")


if __name__ == "__main__":
    main()
