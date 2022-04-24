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
