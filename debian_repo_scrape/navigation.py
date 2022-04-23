import typing as t
from urllib.parse import urljoin
from abc import abstractmethod, ABCMeta
import bs4.element
import requests
from bs4 import BeautifulSoup
from debian.deb822 import Release, Packages
import difflib


class BaseNavigator(metaclass=ABCMeta):
    """
    Base navigator for navigating within a repository

    Overwrite _parse_directions in a subclass for implementing your own behavior
    """

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
        item = item.strip("/")
        curr_url = self.current_url

        if not isinstance(item, str):
            raise TypeError("Requested item must be a string")
        elif "/" in item:
            for subitem in item.split("/"):
                self.navigate(subitem)
                if curr_url == self.current_url:
                    return self
            return self
        elif item not in self.directions:
            raise ValueError(f"{item} is not a valid item for navigation")

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
        elif resp.status_code != 200 and ".." in self.directions:
            self.navigate("..")
        else:
            self._soup = None

    @abstractmethod
    def _parse_directions(self) -> list[str]:
        """
        Parses the possible directions to go to and returns them as a list of strings.
        The string value must be the relative path from the current postition.
        """

    @property
    def directions(self):
        directions = [
            d if "/" not in d else d.split("/")[0] for d in self._parse_directions()
        ]
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
        return str(self)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}{self.directions}"


class PredefinedSuitesNavigator(BaseNavigator):
    """
    Navigator for navigating repositories that give minimal
    access and don't serve any html

    The available suites have to be know before being able to
    be discovered
    """

    def __init__(self, base_url: str, suites: t.Iterable[str]) -> None:
        self._suites_map: dict[str, str] = {suite: [] for suite in suites}
        self._pool: list[str] = []
        if not base_url.endswith("/"):
            base_url += "/"
        for suite in suites:
            suite_release_url = urljoin(base_url, "/".join(["dists", suite, "Release"]))
            resp = requests.get(suite_release_url)
            if resp.status_code != 200:
                continue
            release_file = Release(resp.content.split(b"\n"))
            for file in release_file["SHA256"]:
                filename: str = file["name"]
                self._suites_map[suite].append(filename)
                if filename.endswith("Packages"):
                    packages_url = urljoin(suite_release_url.strip("Release"), filename)
                    resp = requests.get(packages_url)
                    if resp.status_code != 200:
                        continue
                    packages_file = Packages(resp.content.split(b"\n"))
                    if "Filename" in packages_file:
                        self._pool.append(packages_file["Filename"])

        super().__init__(base_url)

    def _parse_directions(self) -> list[str]:
        base_url = self.base_url.strip("/")
        curr_url = self.current_url.strip("/")
        base_url_diff = curr_url[len(base_url) :]
        if base_url == curr_url:
            return ["dists"] + self._pool
        elif base_url_diff == "/dists":
            return [k for k in self._suites_map.keys()]

        elif base_url_diff.startswith("/dists"):
            for suite, paths in self._suites_map.items():
                suite_subpath = f"/dists/{suite}"
                if base_url_diff == suite_subpath:
                    return paths
                elif base_url_diff.startswith(suite_subpath):
                    res = []
                    for path in paths:
                        overlap = base_url_diff[len(suite_subpath) + 1 :]
                        res.append(path[len(overlap) + 1 :])
                    return res

        return [
            path[len(base_url_diff) :]
            for path in self._pool
            if path.startswith(base_url_diff.strip("/"))
        ]


class ApacheBrowseNavigator(BaseNavigator):
    """Navigator for navigating File Browers served by the apache web server"""

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
