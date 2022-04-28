from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

from flask import Flask, abort, render_template, send_file


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

    @app.get("/debian/<path:path>")
    def get_thingy(path: str):
        requested_thingy = os.path.join(os.path.dirname(__file__), "repo", path)
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

    @app.get("/debian/")
    def base():
        return get_thingy("")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
