from os import PathLike
from pgpy import PGPKey, PGPSignature
import requests
from debian_repo_scrape.navigation import BaseNavigator, ApacheBrowseNavigator


def verify_release_signatures(repoURL: str | BaseNavigator, pub_key_file: str):

    navigator = ApacheBrowseNavigator(repoURL) if isinstance(repoURL, str) else repoURL
    pgp_key, _ = PGPKey.from_file(pub_key_file)
    navigator["dists"]
    for dir_ in navigator.directions:
        if dir_ == "..":
            continue
        navigator[f"{dir_}/Release"]
        release_file = navigator.content
        navigator[".."]

        navigator["Release.gpg"]
        release_sig = PGPSignature.from_blob(navigator.content)
        navigator["../.."]
        pgp_key.verify(release_file, release_sig)


def verify_repo_integrity():
    pass
