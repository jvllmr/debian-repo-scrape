from __future__ import annotations

from . import Exporter

try:
    import sqlalchemy as sa
    from sqlalchemy.ext.declarative import DeclarativeMeta
except ImportError:
    raise ImportError(
        "Debian repository SQL export methods are only available with sqlalchemy installed"
    )


def sqlalchemy_model_factory(decl_base: DeclarativeMeta):
    class Respository(decl_base):  # type: ignore
        flat = sa.Column(sa.Boolean, default=False)

    class Suite(decl_base):  # type: ignore
        pass

    class Component(decl_base):  # type: ignore
        pass

    class Package(decl_base):  # type: ignore
        pass

    return Respository, Suite, Component, Package


class SQLExporter(Exporter):
    def __init__(self, sql_url: str):
        pass

    def save(self):
        return super().save()

    def load(self):
        return super().load()
