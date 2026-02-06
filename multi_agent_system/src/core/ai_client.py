
import os
import json
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class AIClient:
    """
    Centralized client for AI interactions. 
    Designed to fail gracefully if no API key is present, falling back to heuristic logic.
    """
    
    def __init__(self):
        if load_dotenv:
            load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.enabled = False
        
        if self.api_key and OpenAI:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.enabled = True
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
        elif not OpenAI:
            print("Warning: 'openai' package not installed. Running in Heuristic Mode.")
        else:
            print("Note: No OPENAI_API_KEY found. Running in Heuristic Mode.")
            
    def complete_json(self, system_prompt: str, user_prompt: str, model: str = "gpt-4o") -> Optional[Dict[str, Any]]:
        """
        Requests a JSON response from the LLM.
        Returns None if AI is disabled or fails.
        """
        if not self.enabled:
            return None
            
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"AI Request Failed: {e}")
            return None

    def complete_text(self, system_prompt: str, user_prompt: str, model: str = "gpt-4o") -> Optional[str]:
        """
        Requests a text response from the LLM.
        Returns None if AI is disabled or fails.
        """
        if not self.enabled:
            return None
            
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"AI Request Failed: {e}")
            return None
