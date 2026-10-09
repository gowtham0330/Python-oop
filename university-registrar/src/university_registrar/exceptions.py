"""Custom exceptions for the University Registrar system.

This module defines a structured exception hierarchy representing domain errors,
validation failures, identity conflicts, and persistence issues.
"""

from typing import Any, Optional


class RegistrarError(Exception):
    """Base exception for all University Registrar errors.

    Attributes:
        message (str): Explanatory error message.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class ValidationError(RegistrarError):
    """Raised when data fails domain validation rules.

    Attributes:
        field (Optional[str]): The attribute or field that failed validation.
        value (Any): The invalid value that was provided.
        message (str): Detailed explanation of why the validation failed.
    """

    def __init__(
        self,
        field: Optional[str] = None,
        value: Any = None,
        message: Optional[str] = None,
    ) -> None:
        self.field = field
        self.value = value
        if message:
            self.detail = message
        elif field:
            self.detail = f"Invalid value {value!r} for field '{field}'"
        else:
            self.detail = "Validation error occurred"

        full_message = f"[{field}] {self.detail}" if field else self.detail
        super().__init__(full_message)


class DuplicateStudentError(RegistrarError):
    """Raised when an operation attempts to register an existing student ID.

    Attributes:
        student_id (str): The conflicting student ID.
    """

    def __init__(self, student_id: str) -> None:
        self.student_id = student_id
        super().__init__(f"Student with ID '{student_id}' already exists in the registrar.")


class StudentNotFoundError(RegistrarError):
    """Raised when a student cannot be found in the registrar.

    Attributes:
        student_id (str): The requested student ID.
    """

    def __init__(self, student_id: str) -> None:
        self.student_id = student_id
        super().__init__(f"Student with ID '{student_id}' was not found in the registrar.")


class StorageError(RegistrarError):
    """Raised when reading, writing, or serializing data fails.

    Attributes:
        message (str): Description of the storage failure.
        path (Optional[str]): Path of the file involved in the failure.
        cause (Optional[Exception]): Underlying system exception, if any.
    """

    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        self.path = path
        self.cause = cause
        detail = f"{message} (path: '{path}')" if path else message
        if cause:
            detail = f"{detail} - Caused by: {cause.__class__.__name__}: {cause}"
        super().__init__(detail)


class UnsupportedFormatError(StorageError):
    """Raised when an unsupported file format or extension is requested.

    Attributes:
        format_name (str): The invalid file format or extension provided.
    """

    def __init__(self, format_name: str, path: Optional[str] = None) -> None:
        self.format_name = format_name
        msg = f"Unsupported file format '{format_name}'. Supported formats are: .json, .csv"
        super().__init__(msg, path=path)
