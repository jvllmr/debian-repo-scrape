from debian_repo_scrape.navigation import BaseNavigator
from debian_repo_scrape.verify import (
    verify_hash_sums,
    verify_release_signatures,
    verify_repo_integrity,
)


def test_signatures(navigator: BaseNavigator):
    verify_release_signatures(navigator, "tests/public_key.gpg")


def test_hash_sums(navigator: BaseNavigator):
    verify_hash_sums(navigator)


def test_verify_both(navigator: BaseNavigator):
    verify_repo_integrity(navigator, "tests/public_key.gpg")
