import typing as t
from urllib.parse import urljoin

import bs4.element
import requests
from bs4 import BeautifulSoup


class PageNavigator:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.current_url = base_url
        self._last_response = requests.get(base_url)
        self._refresh_soup()

    def reset(self):
        """Get back to the base url"""
        self.__init__(self.base_url)
        return self

    def navigate(self, item: str):
        """Navigate to the specified item"""

        if not isinstance(item, str):
            raise TypeError("Requested item must be a string")
        elif item not in self.directions:
            raise ValueError(f"{item} is not a valid item for navigation")

        curr_url = self.current_url
        if not curr_url.endswith("/"):
            curr_url += "/"

        if item == "..":
            new_url = curr_url[: curr_url.strip("/").rindex("/") + 1]
        else:
            new_url = urljoin(curr_url, item)

        self._last_response = requests.get(new_url)
        self.current_url = new_url
        self._refresh_soup()
        return self

    def __getitem__(self, item: str):
        return self.navigate(item)

    def __iter__(self) -> t.Iterator[str]:
        for direction in self.directions:
            yield direction

    def _refresh_soup(self):
        """Refresh our soup object based on our last request"""
        resp = self.last_response
        if resp.status_code == 200 and "text/html" in resp.headers.get(
            "Content-Type", ""
        ):
            self._soup = BeautifulSoup(resp.text, features="html.parser")
        else:
            self._soup = None

    def _parse_directions(self) -> list[str]:
        soup = self.current_soup
        if not soup:
            return []
        links: list[bs4.element.Tag] = soup.pre.find_all("a")

        return [
            child.strip("/")
            for link in links
            for child in link.children
            if isinstance(child, str)
        ]

    @property
    def directions(self):
        directions = self._parse_directions()
        if self.current_url.strip("/").count("/") > 3 and ".." not in directions:
            directions.append("..")
        return directions

    @property
    def last_response(self):
        return self._last_response

    @property
    def current_soup(self):
        return self._soup

    @property
    def content(self):
        """Returns content of latest request response"""
        return self.last_response.text

    def __repr__(self) -> str:
        return repr(self._parse_directions())

    def __str__(self) -> str:
        return str(self._parse_directions())
