# flake8: noqa
from debian_repo_scrape.export.json import JSONExporter
from debian_repo_scrape.navigation import BaseNavigator
from debian_repo_scrape.scrape import scrape_flat_repo, scrape_repo


def test_json(navigator: BaseNavigator):
    repo = scrape_repo(navigator, pub_key_file="tests/public_key.gpg")
    exporter = JSONExporter()
    exporter.append(repo)
    exporter.save("json_export.json")

    loaded_repo = JSONExporter.load("json_export.json")
    assert loaded_repo[0] == repo


def test_json_flat(flat_navigator: BaseNavigator):
    repo = scrape_flat_repo(flat_navigator, pub_key_file="tests/public_key.gpg")
    exporter = JSONExporter()
    exporter.append(repo)
    exporter.save("json_export.json")

    loaded_repo = JSONExporter.load("json_export.json")

    assert loaded_repo[0] == repo
