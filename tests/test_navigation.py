from debian_repo_scrape.navigation import BaseNavigator


def test_navigation(navigator: BaseNavigator):
    assert "dists" in navigator.directions
    assert ".." in navigator.directions
    navigator.navigate("dists")
    assert "mx" in navigator.directions
    navigator[".."]
    assert "dists" in navigator.directions
    navigator["dists"]["mx"]
    assert "main" in navigator


def test_fast_navigation(navigator: BaseNavigator):
    navigator["dists/mx"]
    assert "main" in navigator


def test_reset(navigator: BaseNavigator):
    navigator["dists"]["mx"]["main"]
    assert "binary-armhf" in navigator.directions
    navigator.reset()
    assert "dists" in navigator


def test_file_access(navigator: BaseNavigator):
    navigator["public_key.asc"]
    assert navigator.content.startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----")


def test_checkpoints(navigator: BaseNavigator):
    navigator["dists"]
    navigator.set_checkpoint()
    navigator[".."]
    navigator.use_checkpoint()
    assert navigator.current_url.endswith("/dists/")
    navigator.reset()
