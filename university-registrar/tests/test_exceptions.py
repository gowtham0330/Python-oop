"""Unit tests for custom exception hierarchy."""

import pytest
from university_registrar.exceptions import (
    DuplicateStudentError,
    RegistrarError,
    StudentNotFoundError,
    StorageError,
    UnsupportedFormatError,
    ValidationError,
)


def test_registrar_error_base() -> None:
    """Verify base RegistrarError message handling."""
    err = RegistrarError("General registrar system failure")
    assert str(err) == "General registrar system failure"
    assert isinstance(err, Exception)


def test_validation_error_with_field_and_value() -> None:
    """Verify ValidationError stores field, value, and constructs clear message."""
    err = ValidationError(field="email", value="invalid-email", message="Must contain @")
    assert err.field == "email"
    assert err.value == "invalid-email"
    assert "email" in str(err)
    assert "Must contain @" in str(err)
    assert isinstance(err, RegistrarError)


def test_duplicate_student_error() -> None:
    """Verify DuplicateStudentError captures student ID."""
    err = DuplicateStudentError("UG-2024-001")
    assert err.student_id == "UG-2024-001"
    assert "UG-2024-001" in str(err)
    assert "already exists" in str(err)
    assert isinstance(err, RegistrarError)


def test_student_not_found_error() -> None:
    """Verify StudentNotFoundError captures missing student ID."""
    err = StudentNotFoundError("NON-EXISTENT-99")
    assert err.student_id == "NON-EXISTENT-99"
    assert "NON-EXISTENT-99" in str(err)
    assert "not found" in str(err)
    assert isinstance(err, RegistrarError)


def test_storage_error_with_path_and_cause() -> None:
    """Verify StorageError includes file path and chained cause."""
    cause = PermissionError("Access denied")
    err = StorageError("Disk write failed", path="/var/data.json", cause=cause)
    assert err.path == "/var/data.json"
    assert err.cause is cause
    assert "/var/data.json" in str(err)
    assert "PermissionError" in str(err)
    assert isinstance(err, RegistrarError)


def test_unsupported_format_error() -> None:
    """Verify UnsupportedFormatError inherits from StorageError and mentions format."""
    err = UnsupportedFormatError(".xml", path="test.xml")
    assert err.format_name == ".xml"
    assert ".xml" in str(err)
    assert ".json" in str(err)
    assert isinstance(err, StorageError)
    assert isinstance(err, RegistrarError)
