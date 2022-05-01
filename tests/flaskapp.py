from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, render_template, send_file

from debian_repo_scrape.verify import HASH_FUNCTION_MAP


@dataclass
class Directory:
    date: str
    name: str


@dataclass
class File(Directory):
    size: int


def create_app():
    app = Flask("testapp", template_folder=os.path.dirname(__file__))
    app.config

    def get_thingy(path: str, local_base_path: str):
        requested_thingy = os.path.join(
            os.path.dirname(__file__), local_base_path, path
        )

        if "by-hash" in path:
            hash_ = os.path.basename(path)
            hash_type = path.split("/")[-2].lower()

            for name, arg, _ in HASH_FUNCTION_MAP:
                if name.lower() == hash_type:
                    for path in Path("tests/repo").rglob("*"):
                        try:
                            with open(path, "rb") as f:
                                if hashlib.new(arg, f.read()).hexdigest() == hash_:
                                    return send_file(
                                        path, mimetype="application/octet-stream"
                                    )
                        except IsADirectoryError:
                            continue
            abort(404)

        if path == "forbidden":
            abort(403)
        if os.path.basename(requested_thingy) in (
            "InRelease",
            "Release",
            "Release.gpg",
        ):
            try:
                with open(requested_thingy, "r") as file:
                    return file.read()
            except FileNotFoundError:
                abort(404)

        dirs: list[Directory] = []
        files: list[File] = []

        try:
            obj = os.listdir(requested_thingy)
        except NotADirectoryError:
            return send_file(requested_thingy, mimetype="application/octet-stream")

        for obj in os.listdir(requested_thingy):
            obj_path = os.path.join(requested_thingy, obj)

            mod_time = datetime.fromtimestamp(os.path.getmtime(obj_path))
            mod_time_str: str = mod_time.strftime("%d-%b-%Y %H:%M")
            if os.path.isdir(obj_path):
                dirs.append(Directory(name=obj, date=mod_time_str))
            else:
                files.append(
                    File(name=obj, date=mod_time_str, size=os.path.getsize(obj_path))
                )

        def get_padding(name: str):
            return " " * (51 - len(name))

        return render_template(
            "template.html",
            dirs=dirs,
            files=files,
            basedir=f"/debian/{path}",
            get_padding=get_padding,
        )

    @app.get("/debian/<path:path>")
    def get_debian(path: str):
        return get_thingy(path, "repo")

    @app.get("/debian/")
    def debian_base():
        return get_thingy("", "repo")

    @app.get("/debian_flat/<path:path>")
    def get_debian_flat(path: str):
        return get_thingy(path, "repo_flat")

    @app.get("/debian_flat/")
    def debian_flat_base():
        return get_thingy("", "repo_flat")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
