from typing import List, Dict
import os
import logging

logger = logging.getLogger(__name__)


class LLMProcessor:
    def __init__(self, provider: str = "huggingface"):
        """
        Initialize LLM with multiple provider support.
        
        Args:
            provider: "huggingface" (free, local), "ollama" (free, local), or "openai" (paid)
        """
        self.provider = provider.lower()
        
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "ollama":
            self._init_ollama()
        elif self.provider == "huggingface":
            self._init_huggingface()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        from openai import OpenAI
        
        self.model_name = "gpt-4o-mini"
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"✅ OpenAI LLM initialized: {self.model_name}")
    
    def _init_ollama(self):
        """Initialize Ollama (free local LLM)."""
        import requests
        self.requests = requests
        
        self.model_name = "llama3.2"
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        logger.info(f"✅ Ollama LLM initialized: {self.model_name}")
    
    def _init_huggingface(self):
        """Initialize Hugging Face model (free, runs in Python)."""
        try:
            from transformers import pipeline
            import torch
            
            # Use a small, fast model that works well for Q&A
            self.model_name = "google/flan-t5-base"  # 250MB, good quality
            
            print(f" Loading {self.model_name} (first time may take 1-2 minutes)...")
            
            # Create text generation pipeline
            self.pipe = pipeline(
                "text2text-generation",
                model=self.model_name,
                device="cpu",  # Use CPU (GPU if available will be faster)
                max_length=512
            )
            
            logger.info(f"✅ Hugging Face LLM initialized: {self.model_name}")
            print(f"✅ Model loaded successfully!")
            
        except ImportError:
            raise ImportError(
                "Transformers not installed. Run: pip install transformers torch"
            )
    
    def generate_answer(self, query: str, context: List[Dict]) -> Dict:
        """Generate an answer using the LLM and context."""
        try:
            if self.provider == "openai":
                return self._generate_openai(query, context)
            elif self.provider == "ollama":
                return self._generate_ollama(query, context)
            elif self.provider == "huggingface":
                return self._generate_huggingface(query, context)
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return self._fallback_answer(query, context, error=str(e))
    
    def _generate_openai(self, query: str, context: List[Dict]) -> Dict:
        """Generate using OpenAI."""
        context_text = self._format_context(context)
        
        system_prompt = """You are a helpful music expert assistant. 
        Use the provided context to answer questions about music tracks, artists, and genres.
        Be specific and cite the tracks mentioned in the context when relevant."""
        
        user_prompt = f"""Context (Retrieved Music Tracks):
{context_text}

User Question: {query}

Please provide a helpful answer based on the context above."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        answer = response.choices[0].message.content.strip()
        return {
            "answer": answer,
            "model": f"openai/{self.model_name}",
            "sources_used": len(context),
            "status": "success"
        }
    
    def _generate_ollama(self, query: str, context: List[Dict]) -> Dict:
        """Generate using Ollama (free local LLM)."""
        context_text = self._format_context(context)
        
        prompt = f"""You are a helpful music expert. Use the context below to answer the question.

Context:
{context_text}

Question: {query}

Answer: """

        try:
            response = self.requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            answer = result.get("response", "").strip()
            
            return {
                "answer": answer,
                "model": f"ollama/{self.model_name}",
                "sources_used": len(context),
                "status": "success"
            }
            
        except self.requests.exceptions.ConnectionError:
            raise Exception(
                "Cannot connect to Ollama. Make sure it's running:\n"
                "1. Install: https://ollama.ai\n"
                f"2. Run: ollama pull {self.model_name}\n"
                "3. Ollama runs automatically on port 11434"
            )
        except Exception as e:
            raise Exception(f"Ollama error: {e}")
    
    def _generate_huggingface(self, query: str, context: List[Dict]) -> Dict:
        """Generate using Hugging Face model."""
        context_text = self._format_context_short(context)
        
        # Format prompt for FLAN-T5
        prompt = f"""Answer the question based on the context.

Context: {context_text}

Question: {query}

Answer:"""

        # Generate answer
        result = self.pipe(
            prompt,
            max_length=200,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True
        )
        
        answer = result[0]['generated_text'].strip()
        
        return {
            "answer": answer,
            "model": f"huggingface/{self.model_name}",
            "sources_used": len(context),
            "status": "success"
        }

    def _fallback_answer(self, query: str, context: List[Dict], error: str = None) -> Dict:
        """Provide a fallback answer when LLM fails."""
        tracks_info = [
            f"• {doc.get('track_name', 'Unknown')} by {doc.get('artist_name', 'Unknown')} ({doc.get('genre', 'Unknown')})"
            for doc in context[:5]
        ]

        summary = f"Found {len(context)} relevant tracks for '{query}':\n\n"
        if tracks_info:
            summary += "\n".join(tracks_info)
        else:
            summary += "No matching tracks found."
        
        if error:
            summary += f"\n\n⚠️ Note: LLM error - {error}"
        
        return {
            "answer": summary,
            "sources_used": len(context),
            "model": "fallback",
            "status": "fallback"
        }

    def _format_context(self, context: List[Dict]) -> str:
        """Format documents into text for the LLM."""
        if not context:
            return "No context available."
        
        formatted = []
        for i, doc in enumerate(context, 1):
            track = doc.get('track_name', 'Unknown')
            artist = doc.get('artist_name', 'Unknown')
            genre = doc.get('genre', 'Unknown')
            listeners = doc.get('listeners', 'Unknown')
            
            formatted.append(
                f"{i}. Track: {track}\n"
                f"   Artist: {artist}\n"
                f"   Genre: {genre}\n"
                f"   Listeners: {listeners}"
            )
        
        return "\n\n".join(formatted)
    
    def _format_context_short(self, context: List[Dict]) -> str:
        """Format context more concisely for smaller models."""
        if not context:
            return "No context available."
        
        parts = []
        for doc in context[:3]:  # Limit to top 3 for smaller models
            track = doc.get('track_name', 'Unknown')
            artist = doc.get('artist_name', 'Unknown')
            genre = doc.get('genre', 'Unknown')
            parts.append(f"{track} by {artist} ({genre})")
        
        return ", ".join(parts)

    def test_connection(self) -> bool:
        """Test connection to LLM."""
        try:
            if self.provider == "openai":
                return self._test_openai()
            elif self.provider == "ollama":
                return self._test_ollama()
            elif self.provider == "huggingface":
                return self._test_huggingface()
        except Exception as e:
            logger.error(f" LLM connection failed: {e}")
            return False
    
    def _test_openai(self) -> bool:
        """Test OpenAI connection."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=10
            )
            logger.info(" OpenAI connection successful")
            return True
        except Exception as e:
            logger.error(f" OpenAI failed: {e}")
            return False
    
    def _test_ollama(self) -> bool:
        """Test Ollama connection."""
        try:
            response = self.requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": "Say OK",
                    "stream": False,
                    "options": {"num_predict": 5}
                },
                timeout=30
            )
            response.raise_for_status()
            logger.info(" Ollama connection successful")
            return True
        except Exception as e:
            logger.error(f" Ollama failed: {e}")
            return False
    
    def _test_huggingface(self) -> bool:
        """Test Hugging Face model."""
        try:
            result = self.pipe("Test: Say OK", max_length=10)
            logger.info("✅ Hugging Face model ready")
            return True
        except Exception as e:
            logger.error(f" Hugging Face failed: {e}")
            return False