from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePrompt(ABC):
    """Base class for prompt generators."""

    @abstractmethod
    def format_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the input data into a structured format suitable for the prompt"""
        pass
    
    @abstractmethod
    def build_prompt(self, formatted_data: Dict[str, Any]) -> str:
        """Build the actual prompt string to send to the LLM"""
        pass