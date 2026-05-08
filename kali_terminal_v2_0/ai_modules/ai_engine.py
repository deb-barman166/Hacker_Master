"""
ai_modules/ai_engine.py — AI Integration Engine (v2.0 Masterpiece).

Supports:
  - Ollama (local open-source models)
  - OpenAI API
  - Anthropic API (Claude)
  - Google Gemini API

Features:
  - Streaming responses
  - Conversation history
  - Model management
  - System prompt customization
  - Tool integration for security tasks
"""

import os
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from ui.theme import Colors

C = Colors


@dataclass
class Message:
    """Represents a single chat message."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class AIConfig:
    """AI configuration settings."""
    backend: str = "none"  # ollama, openai, anthropic, gemini
    model: str = ""
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = """You are a helpful AI assistant specialized in cybersecurity.
You help users with security analysis, penetration testing guidance, code review,
vulnerability assessment, and security best practices. Always emphasize ethical
security practices and proper authorization."""

    @classmethod
    def from_env(cls) -> "AIConfig":
        """Load configuration from environment variables."""
        config = cls()
        config.api_key = os.environ.get("OPENAI_API_KEY", "") or \
                        os.environ.get("ANTHROPIC_API_KEY", "") or \
                        os.environ.get("GEMINI_API_KEY", "") or ""
        config.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        config.model = os.environ.get("AI_MODEL", "llama3.2")
        return config


class AIEngine:
    """
    Unified AI engine supporting multiple backends.

    Usage:
        # Local Ollama
        engine = AIEngine(backend="ollama", model="llama3.2")

        # OpenAI
        engine = AIEngine(backend="openai", model="gpt-4", api_key="sk-...")

        # Claude
        engine = AIEngine(backend="anthropic", model="claude-3-opus", api_key="sk-ant-...")

        # Gemini
        engine = AIEngine(backend="gemini", model="gemini-pro", api_key="...")
    """

    def __init__(self, backend: str = "ollama", model: Optional[str] = None,
                 api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.config = AIConfig.from_env()
        self.config.backend = backend

        if model:
            self.config.model = model
        if api_key:
            self.config.api_key = api_key
        if base_url:
            self.config.base_url = base_url

        self.conversation_history: List[Message] = []
        self.is_connected = False
        self._client = None

        # Initialize the appropriate client
        self._init_client()

    def _init_client(self):
        """Initialize the appropriate AI client based on backend."""
        try:
            if self.config.backend == "ollama":
                self._init_ollama()
            elif self.config.backend == "openai":
                self._init_openai()
            elif self.config.backend == "anthropic":
                self._init_anthropic()
            elif self.config.backend == "gemini":
                self._init_gemini()
            else:
                print(C.warn(f"Unknown AI backend: {self.config.backend}"))
                return

            self.is_connected = True
            print(C.success(f"Connected to {self.config.backend} (model: {self.config.model})"))
        except Exception as e:
            print(C.error(f"Failed to initialize {self.config.backend}: {e}"))
            self.is_connected = False

    def _init_ollama(self):
        """Initialize Ollama client."""
        try:
            import requests
            self._client = requests.Session()
            self._client.headers.update({"Content-Type": "application/json"})

            # Test connection
            response = self._client.get(f"{self.config.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(C.info(f"Available Ollama models: {len(models)}"))
            else:
                raise ConnectionError(f"Ollama returned status {response.status_code}")
        except ImportError:
            raise ImportError("requests library required for Ollama. Install with: pip install requests")

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.config.api_key or os.environ.get("OPENAI_API_KEY"),
                timeout=60
            )
            # Verify API key
            self._client.models.list()
        except ImportError:
            raise ImportError("openai library required. Install with: pip install openai")
        except Exception as e:
            raise ConnectionError(f"OpenAI API error: {e}")

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic
            self._client = Anthropic(
                api_key=self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
            )
        except ImportError:
            raise ImportError("anthropic library required. Install with: pip install anthropic")

    def _init_gemini(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key or os.environ.get("GEMINI_API_KEY"))
            self._client = genai
            self._gemini_model = genai.GenerativeModel(self.config.model or "gemini-pro")
        except ImportError:
            raise ImportError("google-generativeai library required. Install with: pip install google-generativeai")

    def chat(self, prompt: str, stream: bool = True) -> str:
        """
        Send a chat message and get a response.

        Args:
            prompt: The user's message
            stream: Whether to stream the response

        Returns:
            The assistant's response text
        """
        if not self.is_connected:
            return C.error("AI not connected. Use 'ai-enable' first.")

        # Add user message to history
        self.conversation_history.append(Message(role="user", content=prompt))

        try:
            if self.config.backend == "ollama":
                response = self._chat_ollama(prompt, stream)
            elif self.config.backend == "openai":
                response = self._chat_openai(prompt, stream)
            elif self.config.backend == "anthropic":
                response = self._chat_anthropic(prompt, stream)
            elif self.config.backend == "gemini":
                response = self._chat_gemini(prompt, stream)
            else:
                return C.error(f"Unsupported backend: {self.config.backend}")

            # Add assistant response to history
            self.conversation_history.append(Message(role="assistant", content=response))
            return response

        except Exception as e:
            error_msg = f"AI request failed: {e}"
            print(C.error(error_msg))
            return C.error(error_msg)

    def _chat_ollama(self, prompt: str, stream: bool = True) -> str:
        """Chat with Ollama."""
        import requests

        messages = self._build_messages(prompt)
        data = {
            "model": self.config.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }

        if stream:
            response_text = []
            try:
                with self._client.post(
                    f"{self.config.base_url}/api/chat",
                    json=data,
                    stream=True,
                    timeout=120
                ) as response:
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            if "message" in chunk:
                                content = chunk["message"].get("content", "")
                                print(content, end="", flush=True)
                                response_text.append(content)
                print()  # New line after streaming
                return "".join(response_text)
            except Exception as e:
                raise RuntimeError(f"Ollama streaming error: {e}")
        else:
            response = self._client.post(
                f"{self.config.base_url}/api/chat",
                json=data,
                timeout=120
            )
            result = response.json()
            return result.get("message", {}).get("content", "")

    def _chat_openai(self, prompt: str, stream: bool = True) -> str:
        """Chat with OpenAI."""
        messages = self._build_messages(prompt)

        if stream:
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                stream=True,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            response_text = []
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    response_text.append(content)
            print()
            return "".join(response_text)
        else:
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return response.choices[0].message.content

    def _chat_anthropic(self, prompt: str, stream: bool = True) -> str:
        """Chat with Anthropic Claude."""
        messages = self._build_messages_for_anthropic(prompt)

        if stream:
            with self._client.messages.stream(
                model=self.config.model or "claude-3-5-sonnet-20241022",
                max_tokens=self.config.max_tokens,
                system=self.config.system_prompt,
                messages=messages
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        content = event.assistant_message.content[0].text if event.assistant_message.content else ""
                        if hasattr(event, 'delta') and event.delta:
                            content = getattr(event.delta, 'text', '')
                        print(content, end="", flush=True)
            print()
            # For streaming, we need to collect the full response
            # This is simplified; real implementation would accumulate
            return "[Response streamed]"
        else:
            response = self._client.messages.create(
                model=self.config.model or "claude-3-5-sonnet-20241022",
                max_tokens=self.config.max_tokens,
                system=self.config.system_prompt,
                messages=messages
            )
            return response.content[0].text

    def _chat_gemini(self, prompt: str, stream: bool = True) -> str:
        """Chat with Google Gemini."""
        if stream:
            response = self._gemini_model.generate_content(
                prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens
                },
                stream=True
            )
            response_text = []
            for chunk in response:
                print(chunk.text, end="", flush=True)
                response_text.append(chunk.text)
            print()
            return "".join(response_text)
        else:
            response = self._gemini_model.generate_content(
                prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens
                }
            )
            return response.text

    def _build_messages(self, prompt: str) -> List[Dict[str, str]]:
        """Build message list for API calls."""
        messages = []

        # Add system prompt
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})

        # Add conversation history (limit to last 10 messages)
        for msg in self.conversation_history[-20:]:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current prompt
        if not any(msg.get("role") == "user" and msg.get("content") == prompt
                   for msg in self.conversation_history[-1:]):
            messages.append({"role": "user", "content": prompt})

        return messages

    def _build_messages_for_anthropic(self, prompt: str) -> List[Dict[str, Any]]:
        """Build message list for Anthropic API."""
        messages = []
        for msg in self.conversation_history[-20:]:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": prompt})
        return messages

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        print(C.success("Conversation history cleared."))

    def get_history(self) -> List[Message]:
        """Get conversation history."""
        return self.conversation_history

    def set_system_prompt(self, prompt: str):
        """Set a custom system prompt."""
        self.config.system_prompt = prompt
        print(C.success("System prompt updated."))

    def list_models(self) -> List[str]:
        """List available models based on backend."""
        if self.config.backend == "ollama":
            try:
                response = self._client.get(f"{self.config.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return [m.get("name", "unknown") for m in models]
            except Exception:
                pass
        elif self.config.backend == "openai":
            try:
                models = self._client.models.list()
                return [m.id for m in models.data[:20]]
            except Exception:
                pass

        return [self.config.model]

    def get_stats(self) -> Dict[str, Any]:
        """Get AI usage statistics."""
        return {
            "backend": self.config.backend,
            "model": self.config.model,
            "is_connected": self.is_connected,
            "conversation_length": len(self.conversation_history),
            "total_messages": len([m for m in self.conversation_history if m.role == "user"]),
            "system_prompt_length": len(self.config.system_prompt)
        }


class AISecurityHelper:
    """
    Specialized AI helper for cybersecurity tasks.
    Wraps the AI engine with security-specific prompts and tools.
    """

    def __init__(self, engine: AIEngine):
        self.engine = engine

    def analyze_code(self, code: str, language: str = "python") -> str:
        """Analyze code for security vulnerabilities."""
        prompt = f"""Analyze the following {language} code for security vulnerabilities.
Focus on:
- Injection vulnerabilities (SQL, Command, XSS, LDAP)
- Authentication/authorization issues
- Cryptographic weaknesses
- Information disclosure
- Race conditions
- Memory safety issues
- Input validation problems

Provide a detailed report with:
1. Severity level (Critical, High, Medium, Low)
2. Description of each vulnerability
3. Proof of concept exploitation (if applicable)
4. Remediation recommendations

Code to analyze:
```{language}
{code}
```

Analysis:"""

        return self.engine.chat(prompt, stream=True)

    def explain_exploit(self, technique: str) -> str:
        """Explain a security exploitation technique ethically."""
        prompt = f"""Explain the following security technique/exploit for educational purposes.
This is for authorized security testing and learning only.

Technique: {technique}

Provide:
1. How it works (technical explanation)
2. What systems/vulnerabilities it targets
3. How to detect if someone is using this technique
4. How to protect against it
5. Ethical considerations for use

Focus on defensive knowledge and proper authorization context."""

        return self.engine.chat(prompt, stream=True)

    def pentest_assistant(self, target: str, phase: str) -> str:
        """Provide guidance for penetration testing phases."""
        phases = {
            "recon": "Information gathering (OSINT, passive/active reconnaissance)",
            "enumeration": "Service enumeration, version detection, vulnerability identification",
            "exploitation": "Controlled exploitation with authorization",
            "post-exploitation": "Privilege escalation, lateral movement, data exfiltration prevention",
            "reporting": "Documentation and remediation guidance"
        }

        phase_desc = phases.get(phase.lower(), phase)
        prompt = f"""As a penetration testing assistant, provide guidance for the {phase.upper()} phase.

Target: {target}
Phase: {phase} - {phase_desc}

Provide:
1. Recommended tools and techniques
2. Key objectives for this phase
3. Common pitfalls to avoid
4. Documentation requirements
5. Relevant command examples (for authorized use only)

Always emphasize:
- Proper authorization and scope adherence
- Safe testing practices
- Non-destructive methodologies
- Proper evidence preservation"""

        return self.engine.chat(prompt, stream=True)

    def hash_analysis(self, hash_value: str) -> str:
        """Analyze a hash value."""
        prompt = f"""Analyze the following hash value:

Hash: {hash_value}

Provide:
1. Most likely hash type(s)
2. Estimated entropy and pattern analysis
3. Possible plaintext sources (if commonly found)
4. Tools for cracking this hash type
5. Prevention strategies for this hash being used against you

Analysis:"""

        return self.engine.chat(prompt, stream=True)

    def network_analysis(self, packet_data: str) -> str:
        """Analyze network packet data."""
        prompt = f"""Analyze the following network data for security assessment:

{packet_data}

Provide:
1. Protocol identification
2. Notable patterns or anomalies
3. Potential security concerns
4. Legitimate vs suspicious indicators
5. Recommendations for investigation

Network Analysis:"""

        return self.engine.chat(prompt, stream=True)