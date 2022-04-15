import requests


def test_server_active():
    resp = requests.get("http://localhost:5000/debian/")
    assert resp.status_code == 200
