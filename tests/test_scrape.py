import os

import requests

from debian_repo_scrape.scrape import scrape_repo


def test_server_active(repo_url: str):
    resp = requests.get(repo_url)
    assert resp.status_code == 200


def test_scrape_test_repo(navigator):
    repo = scrape_repo(navigator, pub_key_file="tests/public_key.gpg")
    assert repo.packages
    for package in repo.packages:
        assert package.name == "poem"
    assert repo.suites
    for suite in repo.suites:
        assert suite.components


class GetPubKey:
    def __init__(self, url: str) -> None:
        self.url = url

    def __enter__(self):
        resp = requests.get(self.url)

        with open("temp_key_file.asc", "wb") as f:
            f.write(resp.content)

    def __exit__(self, *_):
        os.remove("temp_key_file.asc")


def test_scrape_postgresql():
    with GetPubKey("https://ftp.postgresql.org/pub/repos/apt/ACCC4CF8.asc"):
        scrape_repo(
            "https://ftp.postgresql.org/pub/repos/apt/",
            pub_key_file="temp_key_file.asc",
        )


def test_scrape_spotify():
    with GetPubKey("https://download.spotify.com/debian/pubkey_5E3C45D7B312C643.gpg"):
        scrape_repo(
            "https://repository-origin.spotify.com/",
            pub_key_file="temp_key_file.asc",
        )


def test_scrape_nodesource():
    with GetPubKey("https://deb.nodesource.com/gpgkey/nodesource.gpg.key"):
        scrape_repo(
            "https://deb.nodesource.com/node_14.x/",
            pub_key_file="temp_key_file.asc",
        )
