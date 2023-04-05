""" arxiv.org data connector """
import re, feedparser, time
import asyncio, aiohttp

from bookwyrm import models, activitypub
from bookwyrm.settings import SEARCH_TIMEOUT, USER_AGENT
from bookwyrm.book_search import SearchResult
from .abstract_connector import AbstractConnector, Mapping, dict_from_mappings
from .abstract_connector import get_data, infer_physical_format, unique_physical_format
from .connector_manager import ConnectorException, create_edition_task
from .openlibrary_languages import languages

import logging

logger = logging.getLogger(__name__)

class Connector(AbstractConnector):
    """instantiate a connector for Arxiv"""

    generated_remote_link_field = "arxiv_link"

    def __init__(self, identifier):
        super().__init__(identifier)

        get_first = lambda a, *args: a[0]
        get_remote_id = lambda a, *args: self.base_url + a
        get_arxiv_venue = lambda a: ["Arxiv"]
        self.book_mappings = [
            Mapping("title"),
            Mapping("url", remote_field="link"),
            Mapping("id", remote_field="id", formatter=get_arxiv_id),
            Mapping("description", remote_field="summary"),
            Mapping("arxivId", remote_field="id", formatter=get_arxiv_id),
            Mapping(
                "firstPublishedDate",
                remote_field="published",
            ),
            Mapping("publishedDate", remote_field="updated"),
            Mapping("publishers", remote_field="link", formatter=get_arxiv_venue),
        ]

        self.author_mappings = [
            Mapping("name"),
            Mapping("id", remote_field="name", formatter=to_author_id),
        ]

    def get_book_data(self, remote_id):
        remote_id = get_arxiv_id(remote_id)
        data_url = f"{self.books_url}{remote_id}"
        data = feedparser.parse(data_url)
        if len(data.get('entries', [])) > 0:
            return data['entries'][0]
        raise ConnectorException("Unable to get " + remote_id)

    async def get_results(self, session, url, min_confidence, query):
        """try this specific connector"""
        # pylint: disable=line-too-long
        headers = {
            "User-Agent": USER_AGENT,
        }
        params = {"min_confidence": min_confidence}
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if not response.ok:
                    logger.info("Unable to connect to %s: %s", url, response.reason)
                    return
                
                try:
                    raw_data = await response.read()
                    dict_data = feedparser.parse(raw_data)
                except aiohttp.client_exceptions.ContentTypeError as err:
                    logger.exception(err)
                    return
                
                return {
                    "connector": self,
                    "results": self.process_search_response(
                        query, dict_data, min_confidence
                    ),
                }
        except asyncio.TimeoutError:
            logger.info("Connection timed out for url: %s", url)
        except aiohttp.ClientError as err:
            logger.info(err)

    
    def get_remote_id_from_data(self, data):
        """format a url from an arxiv id field"""
        try:
            key = get_arxiv_id(data["id"])
        except KeyError:
            raise ConnectorException("Invalid book data")
        return f"{self.books_url}{key}"

    def is_work_data(self, data):
        return bool(re.match(r"v", get_arxiv_id(data["id"])))

    def get_edition_from_work_data(self, data):
        try:
            key = get_arxiv_id(data["id"])
        except KeyError:
            raise ConnectorException("Invalid book data")
        url = f"{self.books_url}{key}"
        data = self.get_book_data(url)
        edition = pick_default_edition(data["entries"])
        if not edition:
            raise ConnectorException("No editions for work")
        return edition

    def get_work_from_edition_data(self, data):
        try:
            key = get_arxiv_id(data["works"][0]["id"])
        except (IndexError, KeyError):
            raise ConnectorException("No work found for edition")
        url = f"{self.books_url}{key}"
        return self.get_book_data(url)

    def get_or_create_author(self, remote_id):
        """Load author from Arxiv data"""
        existing = models.Author.find_existing_by_remote_id(remote_id)
        if existing:
            return existing
        data = se
    
    def get_authors_from_data(self, data):
        """parse author json and load or create authors"""
        for author_blob in data.get("authors", []):
            author_name = author_blob.get("name")
            # this id is "/authors/OL1234567A"
            author_id = to_author_id(author_name)
            existing = models.Author.find_existing_by_remote_id(author_id)
            if existing:
                yield existing
            mapdata = dict_from_mappings(author_blob, self.author_mappings)
            try:
                activity = activitypub.Author(**mapdata)
            except activitypub.ActivitySerializerError as e:
                logger.error(str(e) + " - Unable to parse " + author_id)
                continue
            author = activity.to_model(model=models.Author, overwrite=False, instance=None)
            if not author:
                continue
            yield author

    def get_or_create_book(self, remote_id):
        return super().get_or_create_book(get_arxiv_id(remote_id))
            
    def parse_search_data(self, data, min_confidence):
        for idx, search_result in enumerate(data.get("entries")):
            # build the remote id from the openlibrary key
            key = self.base_url + get_arxiv_id(search_result["id"])
            author = [i['name'] for i in search_result.get("authors")]

            # Arxiv doesn't provide confidence, but it does sort by an internal ranking, so
            # this confidence value is relative to the list position
            confidence = 1 / (idx + 1)

            yield SearchResult(
                title=search_result.get("title"),
                key=key,
                author=", ".join(author),
                connector=self,
                year=time.strftime("%Y", search_result.get("published_parsed")),
                confidence=confidence,
            )

    def parse_isbn_search_data(self, data):
        return []
        for search_result in list(data.values()):
            # build the remote id from the openlibrary key
            key = self.books_url + search_result["key"]
            authors = search_result.get("authors") or [{"name": "Unknown"}]
            author_names = [author.get("name") for author in authors]
            yield SearchResult(
                title=search_result.get("title"),
                key=key,
                author=", ".join(author_names),
                connector=self,
                year=search_result.get("publish_date"),
            )

    def load_edition_data(self, olkey):
        """query openlibrary for editions of a work"""
        raise ConnectorException("Not implemented")
        url = f"{self.books_url}/works/{olkey}/editions"
        return self.get_book_data(url)

    def expand_book_data(self, book):
        work = book
        raise ConnectorException("Not implemented")
        # go from the edition to the work, if necessary
        if isinstance(book, models.Edition):
            work = book.parent_work

        # we can mass download edition data from OL to avoid repeatedly querying
        try:
            edition_options = self.load_edition_data(work.openlibrary_key)
        except ConnectorException:
            # who knows, man
            return

        for edition_data in edition_options.get("entries"):
            # does this edition have ANY interesting data?
            if ignore_edition(edition_data):
                continue
            create_edition_task.delay(self.connector.id, work.id, edition_data)


def ignore_edition(edition_data):
    """don't load a million editions that have no metadata"""
    return False
    # an isbn, we love to see it
    if edition_data.get("isbn_13") or edition_data.get("isbn_10"):
        return False
    # grudgingly, oclc can stay
    if edition_data.get("oclc_numbers"):
        return False
    # if it has a cover it can stay
    if edition_data.get("covers"):
        return False
    # keep non-english editions
    if edition_data.get("languages") and "languages/eng" not in str(
        edition_data.get("languages")
    ):
        return False
    return True

def to_author_id(s):
    return '/arxiv-author/' + ''.join([i for i in s.lower() if i.isalpha()])

def get_arxiv_id(key):
    """convert /books/OL27320736M into OL27320736M"""
    return key.split("/")[-1]


def get_languages(language_blob):
    """/language/eng -> English"""
    langs = []
    for lang in language_blob:
        langs.append(languages.get(lang.get("key", ""), None))
    return langs


def get_dict_field(blob, field_name):
    """extract the isni from the remote id data for the author"""
    if not blob or not isinstance(blob, dict):
        return None
    return blob.get(field_name)


def pick_default_edition(options):
    """favor physical copies with covers in english"""
    if not options:
        return None
    if len(options) == 1:
        return options[0]

    options = [e for e in options if e.get("covers")] or options
    options = [
        e for e in options if "/languages/eng" in str(e.get("languages"))
    ] or options
    formats = ["paperback", "hardcover", "mass market paperback"]
    options = [
        e for e in options if str(e.get("physical_format")).lower() in formats
    ] or options
    options = [e for e in options if e.get("isbn_13")] or options
    options = [e for e in options if e.get("ocaid")] or options
    return options[0]
