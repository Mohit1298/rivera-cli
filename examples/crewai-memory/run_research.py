#!/usr/bin/env python3
"""
Run 1: Research Agent stores findings in Rivera.

This script demonstrates the Research Agent gathering market intelligence
and storing it as structured, typed memories in Rivera. Run this first,
then run `run_writer.py` separately to prove cross-session persistence.

Usage:
    python run_research.py
"""

from __future__ import annotations

import os
import sys

from crew import build_research_crew
from crewai_rivera import RiveraSetup
from dotenv import load_dotenv

AGENT_ID = "crewai-research-team"
TOPIC = "AI agent frameworks"


def main() -> None:
    load_dotenv()

    api_key = os.environ.get("RIVERA_API_KEY")
    if not api_key:
        print(
            "Error: RIVERA_API_KEY not set. Copy .env.example to .env and fill it in."
        )
        sys.exit(1)

    llm = os.environ.get("CREWAI_LLM", "openrouter/baidu/cobuddy:free")

    # Set up Rivera agent and session
    setup = RiveraSetup(api_key)
    client = setup.setup(
        agent_id=AGENT_ID,
        description="Shared memory for CrewAI research pipeline",
    )

    print(f"\n{'=' * 60}")
    print("  Research Agent - Storing findings in Rivera")
    print(f"  Agent ID: {AGENT_ID}")
    print(f"  Topic: {TOPIC}")
    print(f"{'=' * 60}\n")

    try:
        crew = build_research_crew(client, AGENT_ID, topic=TOPIC, llm=llm)
        result = crew.kickoff()

        print(f"\n{'=' * 60}")
        print("  Research Complete!")
        print(f"{'=' * 60}")
        print(f"\nResult:\n{result}")
        print(
            "\nMemories are now stored in Rivera. Run `python run_writer.py` "
            "to see the Writer Agent retrieve them in a separate session."
        )
    finally:
        setup.teardown(AGENT_ID)


if __name__ == "__main__":
    main()
