"""
LLM Manager for handling different language model providers
"""

import logging
import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt"""
        pass
    
    @abstractmethod
    def generate_with_context(self, prompt: str, context: List[str], **kwargs) -> str:
        """Generate text with additional context"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.model = config.get('model', 'gpt-4')
        self.max_tokens = config.get('max_tokens', 2048)
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 30)
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', self.temperature),
                timeout=kwargs.get('timeout', self.timeout)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_context(self, prompt: str, context: List[str], **kwargs) -> str:
        """Generate text with context using OpenAI API"""
        messages = []
        
        # Add context as system messages
        for ctx in context:
            messages.append({"role": "system", "content": ctx})
        
        # Add the main prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', self.temperature),
                timeout=kwargs.get('timeout', self.timeout)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error generating response: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information"""
        return {
            'provider': 'openai',
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }


class LocalLLMProvider(LLMProvider):
    """Local LLM provider using transformers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_path = config.get('model_path') or os.getenv('LLM_MODEL_PATH')
        self.device = config.get('device', 'auto')
        self.context_length = config.get('context_length', 4096)
        
        if not self.model_path:
            raise ValueError("Local LLM model path not found")
        
        self._load_model()
    
    def _load_model(self):
        """Load the local model"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            # Determine device
            if self.device == 'auto':
                self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
            logger.info(f"Loading local model from {self.model_path} on {self.device}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                device_map=self.device
            )
            
            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
        except ImportError:
            raise ImportError("Transformers package not installed. Run: pip install transformers torch")
        except Exception as e:
            logger.error(f"Error loading local model: {e}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using local model"""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, 
                                  max_length=self.context_length)
            
            if self.device != 'cpu':
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=kwargs.get('max_tokens', 512),
                    temperature=kwargs.get('temperature', 0.7),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the original prompt from the response
            response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_context(self, prompt: str, context: List[str], **kwargs) -> str:
        """Generate text with context using local model"""
        # Combine context and prompt
        full_prompt = "\n\n".join(context) + "\n\n" + prompt
        return self.generate(full_prompt, **kwargs)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get local model information"""
        return {
            'provider': 'local',
            'model_path': self.model_path,
            'device': self.device,
            'context_length': self.context_length
        }


class LLMManager:
    """Manager for different LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = config.get('provider', 'openai')
        self.provider = self._initialize_provider()
        
        logger.info(f"Initialized LLM manager with provider: {self.provider_name}")
    
    def _initialize_provider(self) -> LLMProvider:
        """Initialize the appropriate LLM provider"""
        if self.provider_name == 'openai':
            return OpenAIProvider(self.config)
        elif self.provider_name == 'local':
            return LocalLLMProvider(self.config)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider_name}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the configured provider"""
        return self.provider.generate(prompt, **kwargs)
    
    def generate_with_context(self, prompt: str, context: List[str], **kwargs) -> str:
        """Generate text with context using the configured provider"""
        return self.provider.generate_with_context(prompt, context, **kwargs)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return self.provider.get_model_info()
    
    def switch_provider(self, provider_name: str, config: Dict[str, Any]):
        """Switch to a different LLM provider"""
        self.provider_name = provider_name
        self.config.update(config)
        self.provider = self._initialize_provider()
        logger.info(f"Switched to LLM provider: {provider_name}")
    
    def test_connection(self) -> bool:
        """Test the connection to the LLM provider"""
        try:
            test_prompt = "Hello, this is a test message. Please respond with 'OK' if you can see this."
            response = self.generate(test_prompt, max_tokens=10)
            logger.info(f"LLM connection test successful: {response}")
            return True
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False 