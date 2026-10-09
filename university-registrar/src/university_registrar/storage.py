"""Persistence module providing robust JSON and CSV storage for student records.

Supports atomic file writes, parent directory creation, format validation,
and comprehensive error translation.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Iterable, List, Sequence, Union

from university_registrar.exceptions import (
    StorageError,
    UnsupportedFormatError,
    ValidationError,
)
from university_registrar.models import (
    PostgraduateStudent,
    Student,
    UndergraduateStudent,
)

CSV_FIELDNAMES = [
    "student_id",
    "name",
    "email",
    "age",
    "department",
    "course",
    "semester",
    "cgpa",
    "student_type",
    "academic_advisor",
    "internship_status",
    "research_topic",
    "thesis_supervisor",
]


def _ensure_path(path: Union[str, Path]) -> Path:
    """Convert input to a Path instance."""
    return Path(path)


def _atomic_write_text(target_path: Path, content: str) -> None:
    """Write text to target_path atomically using a temporary file.

    Ensures that interrupted writes never leave corrupted or partially written files.

    Args:
        target_path: Target destination Path.
        content: String content to write with UTF-8 encoding.

    Raises:
        StorageError: If directory creation or write fails.
    """
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StorageError(
            f"Failed to create directory '{target_path.parent}'",
            path=str(target_path),
            cause=exc,
        ) from exc

    temp_file = None
    try:
        # Create temp file in the same directory to allow atomic rename across filesystems
        fd, temp_path_str = tempfile.mkstemp(
            prefix=f".{target_path.name}_",
            suffix=".tmp",
            dir=str(target_path.parent),
            text=True,
        )
        temp_path = Path(temp_path_str)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        # Atomic replace
        temp_path.replace(target_path)
    except OSError as exc:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
        raise StorageError(
            f"Failed to write file atomically to '{target_path}'",
            path=str(target_path),
            cause=exc,
        ) from exc


def save_students_json(
    file_path: Union[str, Path],
    students: Sequence[Student],
) -> None:
    """Serialize student records to a JSON file.

    Args:
        file_path: Destination file path.
        students: Sequence of Student objects to serialize.

    Raises:
        StorageError: If serialization or writing fails.
    """
    path = _ensure_path(file_path)
    try:
        records = [s.to_dict() for s in students]
        payload = {
            "version": "1.0",
            "total_records": len(records),
            "students": records,
        }
        json_content = json.dumps(payload, indent=2, ensure_ascii=False)
        _atomic_write_text(path, json_content)
    except (TypeError, ValueError) as exc:
        raise StorageError(
            "Failed to serialize student records to JSON format",
            path=str(path),
            cause=exc,
        ) from exc


def load_students_json(file_path: Union[str, Path]) -> List[Student]:
    """Load and validate student records from a JSON file.

    Args:
        file_path: Path to the JSON source file.

    Returns:
        List of deserialized Student, UndergraduateStudent, or PostgraduateStudent instances.

    Raises:
        StorageError: If file is missing, unreadable, or malformed JSON.
        ValidationError: If student records inside fail validation.
    """
    path = _ensure_path(file_path)
    if not path.is_file():
        raise StorageError(f"JSON storage file not found: '{path}'", path=str(path))

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise StorageError(
            f"Malformed JSON in file '{path}': {exc.msg} (line {exc.lineno}, col {exc.colno})",
            path=str(path),
            cause=exc,
        ) from exc
    except OSError as exc:
        raise StorageError(
            f"Error reading JSON file '{path}'",
            path=str(path),
            cause=exc,
        ) from exc

    # Support either {"students": [...]} envelope or a direct list [...]
    if isinstance(data, dict):
        if "students" not in data or not isinstance(data["students"], list):
            raise StorageError(
                "JSON root object must contain a 'students' list",
                path=str(path),
            )
        records = data["students"]
    elif isinstance(data, list):
        records = data
    else:
        raise StorageError(
            f"JSON root structure must be an object or list, got {type(data).__name__}",
            path=str(path),
        )

    students: List[Student] = []
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValidationError(
                field=f"students[{idx}]",
                value=record,
                message=f"Student record at index {idx} must be a dictionary.",
            )
        student = Student.from_dict(record)
        students.append(student)

    return students


def export_students_csv(
    file_path: Union[str, Path],
    students: Sequence[Student],
) -> None:
    """Export student records to CSV format with a standardized header.

    Args:
        file_path: Destination CSV file path.
        students: Sequence of Student instances.

    Raises:
        StorageError: If writing fails.
    """
    path = _ensure_path(file_path)
    import io

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=CSV_FIELDNAMES,
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()

    for s in students:
        d = s.to_dict()
        row = {col: d.get(col, "") for col in CSV_FIELDNAMES}
        # Format CGPA consistently to 2 decimals
        row["cgpa"] = f"{float(d.get('cgpa', 0.0)):.2f}"
        row["age"] = str(d.get("age", ""))
        row["semester"] = str(d.get("semester", ""))
        writer.writerow(row)

    _atomic_write_text(path, buffer.getvalue())


def import_students_csv(file_path: Union[str, Path]) -> List[Student]:
    """Import and validate student records from a CSV file.

    Args:
        file_path: Path to the CSV source file.

    Returns:
        List of deserialized Student instances.

    Raises:
        StorageError: If file is missing or unreadable.
        ValidationError: If rows contain missing mandatory fields or invalid data.
    """
    path = _ensure_path(file_path)
    if not path.is_file():
        raise StorageError(f"CSV storage file not found: '{path}'", path=str(path))

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as exc:
        raise StorageError(
            f"Error reading CSV file '{path}'",
            path=str(path),
            cause=exc,
        ) from exc

    if not content.strip():
        # Empty file yields empty list
        return []

    import io

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise StorageError("CSV file contains no valid headers", path=str(path))

    # Required baseline columns
    required_cols = {"student_id", "name", "email", "age", "department", "course", "semester", "cgpa"}
    missing_cols = required_cols - set(reader.fieldnames)
    if missing_cols:
        raise StorageError(
            f"CSV file is missing required columns: {sorted(missing_cols)}",
            path=str(path),
        )

    students: List[Student] = []
    for row_idx, row in enumerate(reader, start=2):  # 1-indexed, header is line 1
        # Convert numeric types
        cleaned_row = dict(row)
        for num_field in ("age", "semester"):
            val = cleaned_row.get(num_field, "").strip()
            if not val:
                raise ValidationError(
                    field=num_field,
                    value=val,
                    message=f"Missing required numeric value on CSV line {row_idx}.",
                )
            try:
                cleaned_row[num_field] = int(val)
            except ValueError as exc:
                raise ValidationError(
                    field=num_field,
                    value=val,
                    message=f"Invalid integer for '{num_field}' on CSV line {row_idx}: {val!r}",
                ) from exc

        cgpa_str = cleaned_row.get("cgpa", "").strip()
        if not cgpa_str:
            raise ValidationError(
                field="cgpa",
                value=cgpa_str,
                message=f"Missing CGPA value on CSV line {row_idx}.",
            )
        try:
            cleaned_row["cgpa"] = float(cgpa_str)
        except ValueError as exc:
            raise ValidationError(
                field="cgpa",
                value=cgpa_str,
                message=f"Invalid CGPA float on CSV line {row_idx}: {cgpa_str!r}",
            ) from exc

        student = Student.from_dict(cleaned_row)
        students.append(student)

    return students


def save_students(
    file_path: Union[str, Path],
    students: Sequence[Student],
) -> None:
    """Save students routing by file extension (.json or .csv).

    Args:
        file_path: Path to target file.
        students: Sequence of students.

    Raises:
        UnsupportedFormatError: If file extension is not .json or .csv.
        StorageError: If storage operation fails.
    """
    path = _ensure_path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        save_students_json(path, students)
    elif suffix == ".csv":
        export_students_csv(path, students)
    else:
        raise UnsupportedFormatError(suffix or "(none)", path=str(path))


def load_students(file_path: Union[str, Path]) -> List[Student]:
    """Load students routing by file extension (.json or .csv).

    Args:
        file_path: Path to source file.

    Returns:
        List of students.

    Raises:
        UnsupportedFormatError: If file extension is not .json or .csv.
        StorageError: If storage operation fails.
    """
    path = _ensure_path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_students_json(path)
    elif suffix == ".csv":
        return import_students_csv(path)
    else:
        raise UnsupportedFormatError(suffix or "(none)", path=str(path))
