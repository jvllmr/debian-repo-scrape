from debian_repo_scrape.navigation import ApacheBrowseNavigator


def test_navigation(apache_navigator: ApacheBrowseNavigator):
    assert "dists" in apache_navigator.directions
    assert ".." in apache_navigator.directions
    apache_navigator.navigate("dists")
    assert "mx" in apache_navigator.directions
    apache_navigator[".."]
    assert "dists" in apache_navigator.directions
    apache_navigator["dists"]["mx"]
    assert "main" in apache_navigator


def test_fast_navigation(apache_navigator: ApacheBrowseNavigator):
    apache_navigator["dists/mx"]
    assert "main" in apache_navigator


def test_reset(apache_navigator: ApacheBrowseNavigator):
    apache_navigator["dists"]["mx"]["main"]
    assert "binary-armhf" in apache_navigator.directions
    apache_navigator.reset()
    assert "dists" in apache_navigator


def test_file_access(apache_navigator: ApacheBrowseNavigator):
    apache_navigator["public_key.asc"]
    assert apache_navigator.content.startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----")
