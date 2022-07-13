import dataclasses
import json

import typing_extensions as te

from debian_repo_scrape.scrape import Component, FlatSuite, Package, Repository, Suite

from . import FileExporter


class CustomJSONDecoder(json.JSONDecoder):
    pass


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Repository):
            return {**dataclasses.asdict(o), "flat": o.flat}

        return super().default(o)


class JSONExporter(FileExporter):
    def _save(self) -> str:
        return json.dumps(self, cls=CustomJSONEncoder)

    @classmethod
    def _load(cls, file_content: str) -> te.Self:  # type: ignore
        repos = cls()
        for repo in json.loads(file_content):
            if repo["flat"]:
                repo.pop("flat")
                for suite in repo["suites"]:
                    suite["package"] = Package.from_dict(suite["package"])
                repo["suites"] = [
                    FlatSuite.from_dict(suite) for suite in repo["suites"]
                ]
                repos.append(Repository.from_dict(repo))
            else:
                repo.pop("flat")
                for suite in repo["suites"]:
                    for component in suite["components"]:
                        component["packages"] = [
                            Package.from_dict(package)
                            for package in component["packages"]
                        ]
                    suite["components"] = [
                        Component.from_dict(component)
                        for component in suite["components"]
                    ]
                repo["suites"] = [Suite.from_dict(suite) for suite in repo["suites"]]
                repos.append(Repository.from_dict(repo))

        return repos
