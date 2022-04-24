import multiprocessing
import time

from flask import Flask
from flaskapp import create_app
from pytest import fixture
from pytest_lazyfixture import lazy_fixture

from debian_repo_scrape.navigation import (
    ApacheBrowseNavigator,
    PredefinedSuitesNavigator,
)


@fixture(scope="session", autouse=True)
def app():

    app = create_app()

    def worker(app: Flask):
        app.run()

    p = multiprocessing.Process(target=worker, args=(app,))
    p.start()
    time.sleep(2)
    yield
    p.terminate()


@fixture()
def repo_url():
    return "http://localhost:5000/debian/"


@fixture()
def apache_navigator(repo_url: str):
    return ApacheBrowseNavigator(repo_url)


@fixture()
def predefined_navigator(repo_url: str):
    return PredefinedSuitesNavigator(repo_url, ["mx"], ["public_key.asc"])


@fixture(
    params=[lazy_fixture("apache_navigator"), lazy_fixture("predefined_navigator")]
)
def navigator(request):
    return request.param
