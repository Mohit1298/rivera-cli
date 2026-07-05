"""
Shared LangGraph state schema for the LangGraph + Mira example.
"""

from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class ResearchState(TypedDict):
    """
    Shared state for the research pipeline.

    Attributes:
        messages: Conversation history (appended by add_messages reducer).
        mira_agent_id: The Mira agent namespace for shared memory.
        research_topic: The current topic being researched.
        findings: Key findings discovered during research.
    """

    messages: Annotated[list[dict], add_messages]
    mira_agent_id: str
    research_topic: str
    findings: list[str]
