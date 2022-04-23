class IntegrityError(Exception):
    pass


class NoDistsPath(Exception):
    message = "Could not find dists folder in repository base"
