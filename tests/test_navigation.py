from debian_repo_check.navigation import PageNavigator


def test_navigation(navigator: PageNavigator):
    assert "dists" in navigator.directions
    assert ".." in navigator.directions
    navigator.navigate("dists")
    assert "mx" in navigator.directions
    navigator[".."]
    assert "dists" in navigator.directions
    navigator["dists"]["mx"]
    assert "main" in navigator


def test_reset(navigator: PageNavigator):
    navigator["dists"]["mx"]["main"]
    assert "binary-armhf" in navigator.directions
    navigator.reset()
    assert "dists" in navigator


def test_file_access(navigator: PageNavigator):
    navigator["public_key.asc"]
    assert navigator.content.startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----")
