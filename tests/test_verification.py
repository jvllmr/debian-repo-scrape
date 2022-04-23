from debian_repo_scrape.navigation import BaseNavigator
from debian_repo_scrape.verify import verify_release_signatures


def test_signatures(navigator: BaseNavigator):
    verify_release_signatures(navigator, "tests/public_key.gpg")
