"""LangChain ``BaseChatModel`` adapter over :class:`BaseLLMProvider`.

The ReAct agents (Node 1 query orchestration, the legacy analysis agent) need a
LangChain chat model. Rather than depend on a per-vendor LangChain integration,
this adapter forwards to whichever provider the active ``llm_mode`` selects, so
the same agent code runs on Groq or on local Qwen.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, Iterator, List, Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class ProviderChatModel(BaseChatModel):
    """Expose a :class:`BaseLLMProvider` as a LangChain chat model.

    Concatenates the message list into a single prompt (plus a system message)
    and returns the raw completion text. That is sufficient for the text-completion
    ReAct format this project uses, where the agent parses ``Thought/Action``
    blocks out of the completion itself rather than using native tool calls.
    """

    provider: Any
    temperature: float = 0.2
    max_tokens: int = 4096

    @property
    def _llm_type(self) -> str:
        return f"hinaing-{type(self.provider).__name__}"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {
            "model": self.provider.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @staticmethod
    def _split_messages(
        messages: List[BaseMessage],
    ) -> tuple[Optional[str], str]:
        """Flatten messages into ``(system_prompt, user_prompt)``."""
        system_chunks: list[str] = []
        conversation: list[str] = []
        for message in messages:
            content = message.content
            text = content if isinstance(content, str) else str(content)
            if message.type == "system":
                system_chunks.append(text)
            else:
                conversation.append(text)
        system_prompt = "\n\n".join(system_chunks) if system_chunks else None
        return system_prompt, "\n\n".join(conversation)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        system_prompt, prompt = self._split_messages(messages)
        extra: dict[str, Any] = {}
        # Groq rejects unknown kwargs, so only forward stop when the caller set it.
        if stop:
            extra["stop"] = stop

        text = asyncio.run(
            self.provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **extra,
            )
        )
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        system_prompt, prompt = self._split_messages(messages)
        extra: dict[str, Any] = {}
        if stop:
            extra["stop"] = stop

        text = await self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **extra,
        )
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        # Streaming is not used by any ReAct call site in this project; emit the
        # completion as a single chunk rather than failing mid-agent.
        yield self._generate(messages, stop=stop, run_manager=run_manager).generations[0]

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGeneration]:
        result = await self._agenerate(messages, stop=stop, run_manager=run_manager)
        yield result.generations[0]
