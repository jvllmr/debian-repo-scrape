import requests


def test_server_active(repo_url):
    resp = requests.get(repo_url)
    assert resp.status_code == 200
