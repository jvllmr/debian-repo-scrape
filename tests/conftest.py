import multiprocessing

from flaskapp import create_app
from pytest import fixture

from debian_repo_scrape.navigation import ApacheBrowseNavigator


@fixture(scope="session", autouse=True)
def app():

    app = create_app()
    p = multiprocessing.Process(target=app.run)
    p.start()

    yield
    p.terminate()


@fixture()
def repo_url():
    return "http://localhost:5000/debian/"


@fixture()
def apache_navigator(repo_url):
    return ApacheBrowseNavigator(repo_url)
