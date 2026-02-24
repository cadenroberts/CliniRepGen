"""
Base Agent - Common functionality for all agents.

Provides:
- LLM client setup
- Tool calling interface
- Logging and error handling
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    
    # LLM settings
    model: str = field(default_factory=lambda: os.getenv("CLINIREPGEN_MODEL", "gpt-4o"))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("API_KEY"))
    api_base: Optional[str] = field(default_factory=lambda: os.getenv("API_BASE", "https://api.openai.com/v1"))
    
    # Generation settings
    temperature: float = 0.0
    max_tokens: int = 4096
    
    # Tool settings
    max_tool_calls: int = 20
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0


class BaseAgent(ABC):
    """
    Base class for all agents.
    
    Provides common functionality like LLM calling and logging.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the agent.
        
        Args:
            config: Agent configuration (uses defaults if not provided)
        """
        self.config = config or AgentConfig()
        
        # Initialize LLM client
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
            timeout=300.0,
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Run the agent's main task."""
        pass
    
    def call_llm(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Call the LLM with messages and optional tools.
        
        Args:
            messages: List of message dicts (role, content)
            tools: Optional list of tool definitions
            response_format: Optional response format spec
            
        Returns:
            Dict with 'content', 'tool_calls', and 'usage'
        """
        call_params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        if tools:
            call_params["tools"] = tools
            call_params["tool_choice"] = "auto"
        
        if response_format:
            call_params["response_format"] = response_format
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.chat.completions.create(**call_params)
                
                message = response.choices[0].message
                
                result = {
                    "content": message.content,
                    "tool_calls": None,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                    }
                }
                
                if message.tool_calls:
                    result["tool_calls"] = [
                        {
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": json.loads(tc.function.arguments),
                        }
                        for tc in message.tool_calls
                    ]
                
                return result
                
            except Exception as e:
                self.logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                import time
                time.sleep(self.config.retry_delay * (2 ** attempt))
        
        raise RuntimeError("LLM call failed after all retries")
    
    def call_llm_json(
        self,
        messages: List[Dict[str, str]],
        schema: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Call the LLM expecting JSON response.
        
        Args:
            messages: List of message dicts
            schema: Optional JSON schema for response
            
        Returns:
            Parsed JSON response
        """
        # Add JSON instruction to system message
        json_instruction = "\nYou must respond with valid JSON only. No other text."
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] += json_instruction
        else:
            messages.insert(0, {"role": "system", "content": json_instruction})
        
        response_format = {"type": "json_object"}
        
        result = self.call_llm(messages, response_format=response_format)
        
        try:
            return json.loads(result["content"])
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Raw response: {result['content']}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
    
    def format_tool_result(self, result: Any) -> str:
        """Format a tool result for inclusion in messages."""
        if isinstance(result, dict):
            return json.dumps(result, indent=2, default=str)
        elif isinstance(result, list):
            return json.dumps(result, indent=2, default=str)
        else:
            return str(result)
