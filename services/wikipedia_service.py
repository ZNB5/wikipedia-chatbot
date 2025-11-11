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
        try:
            page = wikipedia.page(topic, auto_suggest=True)
            sources = self._extract_sources(page)
            logger.info(f"Successfully fetched Wikipedia content for topic: {topic}")
            return page.content, page.summary, sources
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"Disambiguation error for topic {topic}: {e}")
            if e.options[:1]:
                try:
                    page = wikipedia.page(e.options[0], auto_suggest=False)
                    logger.info(f"Successfully fetched Wikipedia content using disambiguation for topic: {topic}")
                    return page.content, page.summary, self._extract_sources(page)
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
        try:
            return [WikipediaSource(title=page.title, url=page.url, excerpt=page.summary[:200] if page.summary else None)]
        except Exception as e:
            logger.error(f"Error extracting source information: {e}")
            return []

    async def get_topic_summary(self, topic: str) -> Optional[str]:
        try:
            return wikipedia.page(topic, auto_suggest=True).summary
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
            return None
        except Exception as e:
            logger.error(f"Error getting topic summary: {e}")
            return None

    async def get_content_from_url(self, url: str) -> Optional[str]:
        try:
            if "/wiki/" not in url:
                logger.error(f"Invalid Wikipedia URL format: {url}")
                return None

            import urllib.parse
            page_title = urllib.parse.unquote(url.split("/wiki/")[-1])
            logger.info(f"Extracting content for page: {page_title} from URL: {url}")

            page = wikipedia.page(page_title, auto_suggest=False)
            logger.info(f"Successfully fetched content from URL: {url}")
            return page.content
        except wikipedia.exceptions.PageError:
            logger.warning(f"Page not found for URL: {url}")
            return None
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"Disambiguation error for URL {url}: {e}")
            if e.options[:1]:
                try:
                    page = wikipedia.page(e.options[0], auto_suggest=False)
                    logger.info(f"Successfully fetched content using disambiguation for URL: {url}")
                    return page.content
                except Exception as ex:
                    logger.error(f"Error fetching disambiguation option: {ex}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching content from URL {url}: {e}")
            return None
