import asyncio
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

CANDIDATE_PATHS = ["/nosotros", "/sobre-nosotros", "/servicios", "/about", "/services"]
MAX_ADDITIONAL_PAGES = 3
MAX_HOME_CHARS = 3000
MAX_ABOUT_CHARS = 4500
REQUEST_TIMEOUT = 10.0
USER_AGENT = "PreviewDiagnosticBot/1.0"


@dataclass
class ScrapedSite:
    home_text: str
    about_text: str


class ScrapingError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


async def _load_robots_parser(client: httpx.AsyncClient, url: str) -> RobotFileParser | None:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = await client.get(robots_url)
    except httpx.HTTPError:
        return None
    if response.status_code >= 400:
        return None
    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser


def _is_allowed(parser: RobotFileParser | None, url: str) -> bool:
    if parser is None:
        return True
    return parser.can_fetch(USER_AGENT, url)


def _extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ", strip=True).split())


async def _fetch_page(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url)
    except httpx.HTTPError:
        return None
    if response.status_code == 404:
        return None
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        return None
    return _extract_visible_text(response.text)


async def fetch_site_text(url: str) -> ScrapedSite:
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            robots_parser = await _load_robots_parser(client, url)
            if not _is_allowed(robots_parser, url):
                raise ScrapingError("robots_disallowed")

            try:
                home_response = await client.get(url)
                home_response.raise_for_status()
            except httpx.TimeoutException as exc:
                raise ScrapingError("timeout") from exc
            except httpx.HTTPError as exc:
                raise ScrapingError(f"fetch_failed: {exc}") from exc

            home_text = _extract_visible_text(home_response.text)
            base_url = str(home_response.url)
            candidate_urls = [
                candidate
                for path in CANDIDATE_PATHS
                if _is_allowed(robots_parser, (candidate := urljoin(base_url, path)))
            ]

            results = await asyncio.gather(
                *(_fetch_page(client, candidate) for candidate in candidate_urls)
            )
            about_pages = [text for text in results if text][:MAX_ADDITIONAL_PAGES]

            return ScrapedSite(
                home_text=home_text[:MAX_HOME_CHARS],
                about_text=" ".join(about_pages)[:MAX_ABOUT_CHARS],
            )
    except ScrapingError:
        raise
    except httpx.TimeoutException as exc:
        raise ScrapingError("timeout") from exc
    except Exception as exc:
        raise ScrapingError(f"unexpected: {exc}") from exc
