class IntegrityError(Exception):
    pass


class NoDistsPath(IntegrityError):
    message = "Could not find dists folder in repository base"


class FileError(IntegrityError):
    def __init__(self, file: str, *args) -> None:
        self.file = file
        super().__init__(*args)


class FileRequestError(FileError):
    def __str__(self) -> str:
        return f"File {self.file} could not requested from the repository"


class HashInvalid(FileError):
    def __str__(self) -> str:
        return f"Hash of {self.file} is invalid"


class MD5SumInvalid(HashInvalid):
    def __str__(self) -> str:
        return f"MD5Sum of {self.file} is invalid"


class SHA1Invalid(HashInvalid):
    def __str__(self) -> str:
        return f"SHA1 of {self.file} is invalid"


class SHA256Invalid(HashInvalid):
    def __str__(self) -> str:
        return f"SHA256 of {self.file} is invalid"
