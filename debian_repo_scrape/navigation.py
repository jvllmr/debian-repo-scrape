from __future__ import annotations

import typing as t
from abc import ABCMeta, abstractmethod
from urllib.parse import urljoin

import bs4.element
from bs4 import BeautifulSoup
from debian.deb822 import Packages, Release

from debian_repo_scrape.utils import _get_response


class BaseNavigator(metaclass=ABCMeta):
    """
    Base navigator for navigating within a repository

    Overwrite _parse_directions in a subclass for implementing your own behavior
    """

    def __init__(self, base_url: str) -> None:
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url = base_url
        self._current_url = base_url
        self._last_response = _get_response(base_url)
        self._soup = None
        self._checkpoints: list[str] = []
        self._refresh_soup()

    def reset(self):
        """Get back to the base url"""
        self._current_url = self.base_url
        self._last_response = _get_response(self.base_url)
        self._refresh_soup()
        return self

    def navigate(self, item: str):
        """Navigate to the specified item"""

        curr_url = self.current_url

        if not isinstance(item, str):
            raise TypeError("Requested item must be a string")

        item = item.strip("/")

        if "/" in item:
            for subitem in item.split("/"):
                self.navigate(subitem)
            return self
        elif item not in self.directions:
            raise ValueError(
                f"{item} is not a valid item for navigation. URL: {self.current_url}"
            )

        if item == "..":
            new_url = curr_url[: curr_url.strip("/").rindex("/") + 1]
        else:
            new_url = urljoin(curr_url, item)

        self._last_response = _get_response(new_url)
        self._current_url = new_url
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
    def _parse_directions(self) -> t.Iterable[str]:
        """
        Parses the possible directions to go to and returns them as a list of strings.
        The string value must be the relative path from the current postition.
        """

    @property
    def directions(self) -> set[str]:
        directions = {
            d if "/" not in d else d.split("/")[0] for d in self._parse_directions()
        }

        if self.current_url.strip("/").count("/") > 2:
            directions.add("..")
        elif ".." in directions:
            directions.remove("..")

        if "" in directions:
            directions.remove("")

        return directions

    @property
    def url_diff(self):
        return self.current_url.strip("/")[
            len(self.base_url.strip("/")) :  # noqa: E203
        ]

    @property
    def url_checkpoint_diff(self):

        if not self.checkpoints:
            raise ValueError("No checkpoint is available.")
        return self.checkpoints[-1]

    @property
    def last_response(self):
        return self._last_response

    @property
    def current_url(self):
        if not self._current_url.endswith("/"):
            self._current_url += "/"
        return self._current_url

    @property
    def current_soup(self):
        return self._soup

    @property
    def content(self):
        """Returns content of latest request response"""
        return self.last_response.text

    def set_checkpoint(self):
        self._checkpoints.append(self.url_diff.strip("/"))

    def use_checkpoint(self):
        self.reset()
        if self.url_checkpoint_diff:
            self.navigate(self.url_checkpoint_diff)
        self._checkpoints.pop()

    def clear_checkpoints(self):
        self._checkpoints = []

    @property
    def checkpoints(self):
        return self._checkpoints

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

    def __init__(
        self,
        base_url: str,
        suites: t.Iterable[str],
        predefined_paths: list[str] | None = None,
        flat_repo: bool = False,
    ) -> None:

        self._paths: list[str] = predefined_paths or []
        if not base_url.endswith("/"):
            base_url += "/"
        for suite in suites:
            release_path = "Release"
            if suite:
                release_path = (
                    f"{suite}/{release_path}"
                    if flat_repo
                    else "/".join(["dists", suite, release_path])
                )

            self._paths.append(release_path)
            release_sig_path = "Release.gpg"
            if suite:
                release_sig_path = (
                    f"{suite}/{release_sig_path}"
                    if flat_repo
                    else "/".join(["dists", suite, release_sig_path])
                )
            self._paths.append(release_sig_path)
            suite_release_url = urljoin(base_url, release_path)
            resp = _get_response(suite_release_url)
            if resp.status_code != 200:
                continue  # pragma: no cover
            release_file = Release(resp.content.split(b"\n"))
            for file in release_file["SHA256"]:
                filename: str = file["name"]
                self._paths.append(
                    f"{suite}/{filename}" if flat_repo else f"dists/{suite}/{filename}"
                )
                if filename.endswith("Packages"):
                    packages_url = urljoin(suite_release_url.strip("Release"), filename)
                    resp = _get_response(packages_url)
                    if resp.status_code != 200:
                        continue  # pragma: no cover
                    packages_file = Packages(resp.content.split(b"\n"))
                    if "Filename" in packages_file:
                        self._paths.append(packages_file["Filename"])

        super().__init__(base_url)

    def _parse_directions(self) -> t.Iterable[str]:

        directions = [
            path[len(self.url_diff) :]  # noqa: E203
            for path in self._paths
            if path.startswith(self.url_diff.lstrip("/"))
            and (
                len(path) >= len(self.url_diff)
                and path[len(self.url_diff) - 1] == "/"
                or not self.url_diff
            )
        ]

        return [direction for direction in directions if direction]


class ApacheBrowseNavigator(BaseNavigator):
    """Navigator for navigating File Browers served by the apache web server"""

    def _parse_directions(self) -> list[str]:
        soup = self.current_soup
        if not soup or not soup.pre:
            if self.base_url == self.current_url:
                return ["dists", "pool"]
            return []
        links: list[bs4.element.Tag] = soup.pre.find_all("a")

        return [
            child.strip("/")
            for link in links
            for child in link.children
            if isinstance(child, str)
        ]
