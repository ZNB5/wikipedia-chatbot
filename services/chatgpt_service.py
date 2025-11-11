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
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "Eres un asistente que extrae temas de preguntas. Extrae SOLO el tema principal en 1-3 palabras. Responde SOLO con el tema, sin explicación."},
                    {"role": "user", "content": f"Pregunta: {question}\n\nTema:"}
                ]
            )
            topic = response.choices[0].message.content.strip()
            logger.info(f"Extracted topic '{topic}' from question: {question}")
            return topic
        except Exception as e:
            logger.error(f"Error extracting topic from question: {e}")
            raise

    async def explain_topic(self, topic: str, wikipedia_content: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "Eres un asistente educativo que explica conceptos de forma clara y sencilla."},
                    {"role": "user", "content": self._build_prompt(topic, wikipedia_content)}
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

    async def get_wikipedia_url_from_question(self, question: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "Eres un asistente que identifica qué artículo de Wikipedia puede responder una pregunta. Responde SOLO con la URL del artículo de Wikipedia en español (https://es.wikipedia.org/wiki/...) que mejor pueda responder la pregunta. No agregues explicaciones ni texto adicional, solo la URL."},
                    {"role": "user", "content": f"Pregunta: {question}\n\nURL de Wikipedia:"}
                ],
            )
            url = response.choices[0].message.content.strip()
            logger.info(f"Extracted Wikipedia URL '{url}' from question: {question}")
            return url
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
            logger.error(f"Error getting Wikipedia URL from question: {e}")
            raise OpenAIException(str(e), "OPENAI_ERROR")

    async def answer_question_with_wikipedia(self, question: str, wikipedia_content: str, wikipedia_url: str) -> str:
        try:
            prompt = f"""Basándote EXCLUSIVAMENTE en la siguiente información de Wikipedia, responde la siguiente pregunta de forma clara y precisa.

Pregunta: {question}

Información de Wikipedia:
{wikipedia_content[:4000]}

Responde de forma directa y precisa, usando un lenguaje simple. No agregues información que no esté en el texto. Responde solo con la respuesta, sin agregar "Respuesta:" ni ningún prefijo."""

            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "Eres un asistente educativo que responde preguntas basándose únicamente en información proporcionada."},
                    {"role": "user", "content": prompt}
                ],
            )
            answer = response.choices[0].message.content.strip()
            logger.info(f"Successfully generated answer for question: {question}")
            return f"{answer}. Fuente: {wikipedia_url}"
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
            logger.error(f"Unexpected error answering question: {e}")
            raise OpenAIException(str(e), "OPENAI_ERROR")

    def _build_prompt(self, topic: str, wikipedia_content: str) -> str:
        return f"""Basándote EXCLUSIVAMENTE en la siguiente información de Wikipedia, explícame de forma sencilla qué es {topic}.

Información de Wikipedia:
{wikipedia_content[:2000]}

Usa un lenguaje simple y comprensible. Mantén la explicación breve (máximo 3 párrafos). No agregues información que no esté en el texto proporcionado."""
