from __future__ import annotations

import os
import typing as t
from abc import ABCMeta, abstractmethod
from io import BufferedReader, BufferedWriter, TextIOWrapper

import typing_extensions as te

from debian_repo_scrape.scrape import Repository


class Exporter(t.List[Repository], metaclass=ABCMeta):
    @abstractmethod
    def save(self):
        """Write repository infos to the exporter-specific output format"""

    @classmethod
    @abstractmethod
    def load(cls, *args, **kwargs) -> te.Self:  # type: ignore
        """Read repository infos from the exporter-specific output format"""


class FileExporter(Exporter, metaclass=ABCMeta):
    def save(self, file: str | os.PathLike | BufferedWriter | TextIOWrapper):  # type: ignore
        if isinstance(file, (str, os.PathLike)):
            with open(file, "w") as f:
                f.write(self._save())
        elif isinstance(file, BufferedWriter):
            file.write(self._save().encode("utf-8"))
        elif isinstance(file, TextIOWrapper):
            file.write(self._save())
        else:
            raise TypeError(f"{type(file)} is not a valid type")

    @abstractmethod
    def _save(self) -> str:
        pass

    @classmethod
    def load(cls, file: str | os.PathLike | BufferedReader | TextIOWrapper):  # type: ignore
        if isinstance(file, (str, os.PathLike)):
            with open(file, "r") as f:
                file_content = f.read()
        elif isinstance(file, BufferedReader):
            file_content = file.read().decode("utf-8")
        elif isinstance(file, TextIOWrapper):
            file_content = file.read()
        else:
            raise TypeError(f"{type(file)} is not a valid type")

        return cls._load(file_content)

    @classmethod
    @abstractmethod
    def _load(cls, file_content: str) -> te.Self:  # type: ignore
        pass
