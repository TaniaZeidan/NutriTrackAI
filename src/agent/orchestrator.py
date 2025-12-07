"""Agent orchestration using LangChain."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependencies
    from langchain.agents import (
        AgentExecutor,
        AgentType,
        Tool,
        initialize_agent,
    )
    from langchain.memory import ConversationBufferMemory
except Exception:  # pragma: no cover
    AgentExecutor = None  # type: ignore
    Tool = None  # type: ignore
    ConversationBufferMemory = None  # type: ignore

ChatGoogleGenerativeAI = None
try:  # pragma: no cover - prefer dedicated package
    from langchain_google_genai import ChatGoogleGenerativeAI as _GoogleChat  # type: ignore
    ChatGoogleGenerativeAI = _GoogleChat
except Exception:
    try:
        from langchain_community.chat_models import ChatGoogleGenerativeAI as _GoogleChat  # type: ignore
        ChatGoogleGenerativeAI = _GoogleChat
    except Exception:
        ChatGoogleGenerativeAI = None  # type: ignore


from config import CHAT_MODEL
from core.llm import GeminiClient
from core.memory import ConversationMemory, PreferenceMemory
from core.prompts import SYSTEM_PROMPT


class NutriTrackAgent:
    """High-level facade for executing agent workflows."""

    def __init__(
        self,
        tools: List[Any],
        gemini: GeminiClient | None = None,
        conversation: ConversationMemory | None = None,
        preferences: PreferenceMemory | None = None,
    ) -> None:
        self.tools = tools
        self.gemini = gemini or GeminiClient()
        self.conversation = conversation or ConversationMemory()
        self.preferences = preferences or PreferenceMemory()
        self.memory: Optional[ConversationBufferMemory] = None
        self._executor = self._build_executor()

    def _build_executor(self):  # pragma: no cover - mostly integration logic
        if AgentExecutor and ChatGoogleGenerativeAI:
            try:
                self.memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True,
                )
                llm = ChatGoogleGenerativeAI(
                    model=CHAT_MODEL,
                    convert_system_message_to_human=True,
                )
                agent = initialize_agent(
                    tools=self.tools,
                    llm=llm,
                    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                    verbose=False,
                    memory=self.memory,
                    handle_parsing_errors=True,
                    agent_kwargs={"system_message": SYSTEM_PROMPT},
                )
                return agent
            except Exception as exc:
                print(f"Failed to initialize LangChain agent, falling back to GeminiClient: {exc}")
                return None
        return None

    def run(self, prompt: str) -> str:
        """Execute the agent against a prompt."""
        self.conversation.add_turn(prompt, "")
        if self._executor:
            result = self._executor.run(prompt)
        else:
            result = self.gemini.generate_text(prompt)
        self.conversation.buffer[-1] = (prompt, result)
        return result


__all__ = ["NutriTrackAgent"]
