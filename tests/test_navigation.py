from __future__ import annotations

import pytest

from debian_repo_scrape.navigation import BaseNavigator


def test_navigation(navigator: BaseNavigator, repo_url: str):
    assert navigator.base_url == repo_url
    assert "dists" in navigator.directions
    assert ".." in navigator.directions
    navigator.navigate("dists")
    assert "mx" in navigator.directions
    navigator[".."]
    assert "dists" in navigator.directions
    navigator["dists"]["mx"]
    assert navigator.current_url == f"{repo_url}dists/mx/"
    assert "main" in navigator
    navigator[".."][".."]
    navigator["dists/focal/stable"]
    assert navigator.current_url == f"{repo_url}dists/focal/stable/"
    navigator.reset()
    navigator["forbidden"]
    assert navigator.current_url == navigator.base_url
    with pytest.raises(ValueError):
        navigator["ehrguerzzuge"]

    with pytest.raises(TypeError):
        navigator[0]


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
    navigator["dists"]
    navigator.set_checkpoint()
    navigator["focal"]
    navigator.set_checkpoint()
    navigator["stable"]
    navigator.set_checkpoint()
    navigator["Release"]
    navigator.use_checkpoint()
    assert navigator.current_url.endswith("focal/stable/")
    navigator.use_checkpoint()
    assert navigator.current_url.endswith("dists/focal/")
    navigator.clear_checkpoints()
    with pytest.raises(ValueError):
        navigator.use_checkpoint()


def test_directions(navigator: BaseNavigator):
    assert ".." in navigator.directions
    navigator.base_url = "http://localhost:5000/"
    navigator.reset()
    assert ".." not in navigator.directions
    navigator.base_url = "http://localhost:5000"
    navigator.reset()
    assert ".." not in navigator.directions
