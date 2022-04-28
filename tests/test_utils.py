from debian_repo_scrape.utils import _get_file, get_packages_files, get_suites


def test_get_suites(navigator):
    suites = get_suites(navigator)
    assert "mx" in suites
    assert "focal/stable" in suites


def test_get_packages_files(repo_url):
    assert get_packages_files(repo_url.strip("/"), "mx") == get_packages_files(
        repo_url, "mx"
    )


def test_get_file(repo_url):
    assert _get_file(repo_url.strip("/"), "public_key.asc") == _get_file(
        repo_url, "public_key.asc"
    )
