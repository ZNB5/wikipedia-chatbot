import wikipedia
import logging
from typing import Optional, Tuple, List
from schemas.response import WikipediaSource


logger = logging.getLogger(__name__)


class WikipediaService:
    """Service for fetching information from Wikipedia"""

    def __init__(self):
        wikipedia.set_lang('es')  # Set language to Spanish

    async def search_topic(self, topic: str) -> Optional[Tuple[str, str, List[WikipediaSource]]]:
        """
        Search for a topic on Wikipedia and return content and sources.

        Args:
            topic: The topic to search for

        Returns:
            Tuple of (content, summary, sources) or None if not found
        """
        try:
            # Try to get the page
            page = wikipedia.page(topic, auto_suggest=True)

            # Extract sources
            sources = self._extract_sources(page)

            # Get the summary and content
            summary = page.summary
            content = page.content

            logger.info(f"Successfully fetched Wikipedia content for topic: {topic}")
            return content, summary, sources

        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"Disambiguation error for topic {topic}: {e}")
            # Try with the first option
            options = e.options[:3]  # Get first 3 options
            if options:
                try:
                    page = wikipedia.page(options[0], auto_suggest=False)
                    sources = self._extract_sources(page)
                    summary = page.summary
                    content = page.content
                    logger.info(f"Successfully fetched Wikipedia content using disambiguation for topic: {topic}")
                    return content, summary, sources
                except Exception as ex:
                    logger.error(f"Error fetching disambiguation option: {ex}")
                    return None

        except wikipedia.exceptions.PageError:
            logger.warning(f"Page not found for topic: {topic}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching Wikipedia content: {e}")
            return None

    def _extract_sources(self, page) -> List[WikipediaSource]:
        """Extract source information from Wikipedia page"""
        sources = []

        try:
            source = WikipediaSource(
                title=page.title,
                url=page.url,
                excerpt=page.summary[:200] if page.summary else None
            )
            sources.append(source)
        except Exception as e:
            logger.error(f"Error extracting source information: {e}")

        return sources

    async def get_topic_summary(self, topic: str) -> Optional[str]:
        """Get a brief summary of a topic from Wikipedia"""
        try:
            page = wikipedia.page(topic, auto_suggest=True)
            return page.summary
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
            return None
        except Exception as e:
            logger.error(f"Error getting topic summary: {e}")
            return None
