"""
LangChain agent setup for Orchestrator.
Creates Claude-powered agent with tool calling capabilities.
"""

import logging
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from django.conf import settings

from .tools import ALL_TOOLS
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Global agent instance (singleton for performance)
_agent_executor = None


def create_orchestrator_agent():
    """
    Create LangChain agent with Claude and all tools.

    Returns:
        AgentExecutor: Configured agent ready for use
    """
    # Initialize Claude LLM
    llm = ChatAnthropic(
        model=settings.ANTHROPIC_MODEL,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=2048,
        temperature=0.1  # Lower temperature for more consistent behavior
    )

    # Create ReAct-style prompt
    template = SYSTEM_PROMPT + """

TOOLS:
You have access to the following tools:

{tools}

Use the following format:

Thought: I need to think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final response to the user in markdown format

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""

    prompt = PromptTemplate.from_template(template)

    # Create ReAct agent
    agent = create_react_agent(llm, ALL_TOOLS, prompt)

    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=True,  # Log tool calls for debugging
        max_iterations=15,  # Prevent infinite loops
        handle_parsing_errors=True,  # Graceful error handling
        return_intermediate_steps=False  # Don't return tool call details to user
    )

    logger.info("Orchestrator agent created with 8 tools")
    return agent_executor


def get_orchestrator_agent():
    """
    Get or create singleton orchestrator agent.

    Returns:
        AgentExecutor: The orchestrator agent
    """
    global _agent_executor

    if _agent_executor is None:
        _agent_executor = create_orchestrator_agent()

    return _agent_executor


def reset_agent():
    """Reset the agent (for testing)"""
    global _agent_executor
    _agent_executor = None
