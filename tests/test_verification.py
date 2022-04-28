import os

import pytest

from debian_repo_scrape.exc import FileRequestError, HashInvalid
from debian_repo_scrape.navigation import BaseNavigator
from debian_repo_scrape.utils import clear_response_cache
from debian_repo_scrape.verify import (
    verify_hash_sums,
    verify_release_signatures,
    verify_repo_integrity,
)

keyfile = "tests/public_key.gpg"


class RemoveFile:
    def __init__(self, path: str) -> None:
        self.path = path
        self.file_content = b""

    def __enter__(self):
        with open(self.path, "rb") as f:
            self.file_content = f.read()
        os.remove(self.path)
        clear_response_cache()
        return self

    def __exit__(self, *_):
        with open(self.path, "wb") as f:
            f.write(self.file_content)
        clear_response_cache()


class ModifyFile:
    def __init__(self, path: str) -> None:
        self.path = path
        self.file_content = b""

    def __enter__(self):
        with open(self.path, "rb") as f:
            self.file_content = f.read()
        with open(self.path, "wb") as f:
            f.write(self.file_content + b"\n\n\n1234")

        clear_response_cache()
        return self

    def __exit__(self, *_):
        with open(self.path, "wb") as f:
            f.write(self.file_content)
        clear_response_cache()


def test_signatures(navigator: BaseNavigator):

    verify_release_signatures(navigator, keyfile)

    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/dists/mx/Release"):
            verify_release_signatures(navigator, keyfile)

    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/dists/mx/Release.gpg"):
            verify_release_signatures(navigator, keyfile)


def test_hash_sums(navigator: BaseNavigator):
    verify_hash_sums(navigator)
    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/dists/mx/main/binary-amd64/Packages"):
            verify_hash_sums(navigator)

    with RemoveFile("tests/repo/dists/mx/main/binary-amd64/Packages.gz"):
        verify_hash_sums(navigator)

    with pytest.raises(HashInvalid):
        with ModifyFile("tests/repo/dists/mx/main/binary-amd64/Packages"):
            verify_hash_sums(navigator)

    with pytest.raises(HashInvalid):
        with ModifyFile("tests/repo/pool/main/p/poem/poem_1.0_all.deb"):
            verify_hash_sums(navigator)


def test_verify_both(navigator: BaseNavigator):
    verify_repo_integrity(navigator, keyfile)
