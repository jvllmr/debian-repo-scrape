from flaskapp import create_app
from pytest import fixture
from pytest_flask.live_server import LiveServer
from pytest_lazyfixture import lazy_fixture

from debian_repo_scrape.navigation import (
    ApacheBrowseNavigator,
    PredefinedSuitesNavigator,
)


@fixture(scope="session")
def app():
    return create_app()


@fixture(scope="session", autouse=True)
def start_server(live_server: LiveServer):
    pass


@fixture()
def repo_url():
    return "http://localhost:5000/debian/"


@fixture()
def flat_repo_url():
    return "http://localhost:5000/debian_flat/"


@fixture()
def apache_navigator(repo_url: str):
    return ApacheBrowseNavigator(repo_url.strip("/"))


@fixture()
def flat_apache_navigator(flat_repo_url: str):
    return ApacheBrowseNavigator(flat_repo_url.strip("/"))


@fixture()
def predefined_navigator(repo_url: str):
    return PredefinedSuitesNavigator(
        repo_url.strip("/"), ["mx", "focal/stable"], ["public_key.asc", "forbidden"]
    )


@fixture()
def flat_predefined_navigator(flat_repo_url: str):
    return PredefinedSuitesNavigator(
        flat_repo_url.strip("/"),
        ["", "wheezy", "bullseye/stable"],
        ["public_key.asc"],
        flat_repo=True,
    )


@fixture(
    params=[lazy_fixture("apache_navigator"), lazy_fixture("predefined_navigator")]
)
def navigator(request):
    return request.param


@fixture(
    params=[
        lazy_fixture("flat_apache_navigator"),
        lazy_fixture("flat_predefined_navigator"),
    ]
)
def flat_navigator(request):
    return request.param
