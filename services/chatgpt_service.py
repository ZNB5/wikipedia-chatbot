from openai import OpenAI, AuthenticationError, RateLimitError, APIError
import logging
from config.settings import settings
from utils.exceptions import (
    AuthenticationException as ChatbotAuthError,
    RateLimitException as ChatbotRateLimitError,
    OpenAIException
)


logger = logging.getLogger(__name__)


class ChatGPTService:
    """Service for interacting with OpenAI's ChatGPT"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    async def extract_topic_from_question(self, question: str) -> str:
        """
        Extract the main topic from a user question.

        Args:
            question: The user's question

        Returns:
            The extracted topic name
        """
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente que extrae temas de preguntas. Extrae SOLO el tema principal en 1-3 palabras. Responde SOLO con el tema, sin explicación."
                    },
                    {
                        "role": "user",
                        "content": f"Pregunta: {question}\n\nTema:"
                    }
                ]
            )

            topic = response.choices[0].message.content.strip()
            logger.info(f"Extracted topic '{topic}' from question: {question}")
            return topic

        except Exception as e:
            logger.error(f"Error extracting topic from question: {e}")
            raise

    async def explain_topic(self, topic: str, wikipedia_content: str) -> str:
        """
        Use ChatGPT to explain a topic based on Wikipedia content.

        Args:
            topic: The topic to explain
            wikipedia_content: The Wikipedia content about the topic

        Returns:
            Explanation from ChatGPT
        """
        try:
            prompt = self._build_prompt(topic, wikipedia_content)

            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente educativo que explica conceptos de forma clara y sencilla."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            explanation = response.choices[0].message.content.strip()
            logger.info(f"Successfully generated explanation for topic: {topic}")
            return explanation

        except AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            raise ChatbotAuthError(str(e))

        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded: {e}")
            raise ChatbotRateLimitError(str(e))

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIException(str(e), "OPENAI_API_ERROR")

        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise OpenAIException(str(e), "OPENAI_ERROR")

    def _build_prompt(self, topic: str, wikipedia_content: str) -> str:
        """Build the prompt for ChatGPT"""
        return f"""
Basándote EXCLUSIVAMENTE en la siguiente información de Wikipedia,
explícame de forma sencilla qué es {topic}.

Información de Wikipedia:
{wikipedia_content[:2000]}

Por favor:
1. Usa un lenguaje simple y comprensible
2. Mantén la explicación breve (máximo 3 párrafos)
3. No agregues información que no esté en el texto proporcionado
4. Si la información no es suficiente, indícalo
"""
