from debian_repo_scrape.utils import get_suites


def test_gest_suites(navigator):
    assert get_suites(navigator) == ["mx", "focal/stable"]
