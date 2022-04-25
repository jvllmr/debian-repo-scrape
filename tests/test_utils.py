from debian_repo_scrape.utils import get_suites


def test_gest_suites(navigator):
    suites = get_suites(navigator)
    assert "mx" in suites
    assert "focal/stable" in suites
