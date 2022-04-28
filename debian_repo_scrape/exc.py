# pragma: nocover
from __future__ import annotations


class IntegrityError(Exception):
    pass


class NoDistsPath(IntegrityError):
    message = "Could not find dists folder in repository base"


class FileError(IntegrityError):
    def __init__(self, file: str, file_mentioned_by: str | None = None, *args) -> None:
        self.file = file
        self.file_mentioned_by = file_mentioned_by
        super().__init__(*args)


class FileRequestError(FileError):
    def __init__(
        self, file: str, status_code: str, file_mentioned_by: str | None = None, *args
    ) -> None:
        self.status_code = status_code
        super().__init__(file, file_mentioned_by, *args)

    def __str__(self) -> str:
        fill = " "
        if self.file_mentioned_by:
            fill = f", mentioned in {self.file_mentioned_by},"

        return f"File {self.file}{fill}could not be requested from the repository - Status Code: {self.status_code}"  # noqa: E501


class HashInvalid(FileError):
    def __init__(self, file: str, file_mentioned_by: str, *args) -> None:
        super().__init__(file, file_mentioned_by, *args)

    def __str__(self) -> str:
        return f"Hash of {self.file} mentioned in {self.file_mentioned_by} is invalid"


class MD5SumInvalid(HashInvalid):
    def __str__(self) -> str:
        return f"MD5Sum of {self.file} mentioned in {self.file_mentioned_by} is invalid"


class SHA1Invalid(HashInvalid):
    def __str__(self) -> str:
        return f"SHA1 of {self.file} mentioned in {self.file_mentioned_by} is invalid"


class SHA256Invalid(HashInvalid):
    def __str__(self) -> str:
        return f"SHA256 of {self.file} mentioned in {self.file_mentioned_by} is invalid"
