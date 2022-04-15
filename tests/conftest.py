import multiprocessing

from flaskapp import create_app
from pytest import fixture


@fixture(scope="session", autouse=True)
def app():

    app = create_app()
    p = multiprocessing.Process(target=app.run)
    p.start()

    yield
    p.terminate()
