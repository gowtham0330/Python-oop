"""Input validation functions for person and student data.

All validators raise custom `ValidationError` instances with the target field name,
the problematic value, and an informative explanation of the rule violated.
"""

import re
from typing import Any, Optional
from university_registrar.exceptions import ValidationError

# RFC 5322 compliant simplified email regex
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_name(name: Any) -> str:
    """Validate a person's full name.

    Args:
        name: Name string to validate.

    Returns:
        Stripped valid name string.

    Raises:
        ValidationError: If name is not a string, is empty, or contains invalid characters.
    """
    if not isinstance(name, str):
        raise ValidationError(
            field="name",
            value=name,
            message="Name must be a non-empty string.",
        )
    cleaned = name.strip()
    if len(cleaned) < 1:
        raise ValidationError(
            field="name",
            value=name,
            message="Name must not be empty.",
        )
    # Reject strings composed purely of numbers or punctuation
    if not any(c.isalpha() for c in cleaned):
        raise ValidationError(
            field="name",
            value=name,
            message="Name must contain at least one alphabetic character.",
        )
    return cleaned


def validate_email(email: Any) -> str:
    """Validate an email address according to standard email format.

    Args:
        email: Email string to validate.

    Returns:
        Stripped lowercase valid email address.

    Raises:
        ValidationError: If email is missing, malformed, or has invalid syntax.
    """
    if not isinstance(email, str):
        raise ValidationError(
            field="email",
            value=email,
            message="Email address must be a string.",
        )
    cleaned = email.strip()
    if not cleaned or not EMAIL_REGEX.match(cleaned):
        raise ValidationError(
            field="email",
            value=email,
            message="Email must be in a valid format (e.g., student@university.edu).",
        )
    return cleaned.lower()


def validate_age(age: Any, min_age: int = 16, max_age: int = 100) -> int:
    """Validate age as a positive integer within human academic boundaries.

    Args:
        age: Age value (int or string convertible to int).
        min_age: Minimum acceptable age (default 16).
        max_age: Maximum acceptable age (default 100).

    Returns:
        Integer age.

    Raises:
        ValidationError: If age cannot be parsed to an int or falls outside bounds.
    """
    if isinstance(age, bool):  # Python bool is a subclass of int
        raise ValidationError(
            field="age",
            value=age,
            message="Age cannot be a boolean value.",
        )

    try:
        age_int = int(age)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            field="age",
            value=age,
            message=f"Age must be a valid integer, got {type(age).__name__}.",
        ) from exc

    if age_int < min_age or age_int > max_age:
        raise ValidationError(
            field="age",
            value=age,
            message=f"Age must be between {min_age} and {max_age} years, got {age_int}.",
        )
    return age_int


def validate_student_id(student_id: Any) -> str:
    """Validate student identification string.

    Args:
        student_id: Student identifier.

    Returns:
        Stripped student ID string.

    Raises:
        ValidationError: If student ID is empty, whitespace, or invalid type.
    """
    if not isinstance(student_id, str):
        raise ValidationError(
            field="student_id",
            value=student_id,
            message="Student ID must be a non-empty string.",
        )
    cleaned = student_id.strip()
    if not cleaned:
        raise ValidationError(
            field="student_id",
            value=student_id,
            message="Student ID cannot be empty or whitespace.",
        )
    return cleaned


def validate_department(department: Any) -> str:
    """Validate academic department name.

    Args:
        department: Department name.

    Returns:
        Stripped department string.

    Raises:
        ValidationError: If department is missing, empty, or not a string.
    """
    if not isinstance(department, str):
        raise ValidationError(
            field="department",
            value=department,
            message="Department must be a string.",
        )
    cleaned = department.strip()
    if not cleaned:
        raise ValidationError(
            field="department",
            value=department,
            message="Department cannot be empty.",
        )
    return cleaned


def validate_course(course: Any) -> str:
    """Validate course / program of study name.

    Args:
        course: Course name.

    Returns:
        Stripped course string.

    Raises:
        ValidationError: If course is missing, empty, or not a string.
    """
    if not isinstance(course, str):
        raise ValidationError(
            field="course",
            value=course,
            message="Course must be a string.",
        )
    cleaned = course.strip()
    if not cleaned:
        raise ValidationError(
            field="course",
            value=course,
            message="Course name cannot be empty.",
        )
    return cleaned


def validate_semester(
    semester: Any,
    min_semester: int = 1,
    max_semester: int = 12,
) -> int:
    """Validate current semester number within configurable boundaries.

    Args:
        semester: Semester value.
        min_semester: Minimum semester number (default 1).
        max_semester: Maximum semester number (default 12).

    Returns:
        Integer semester.

    Raises:
        ValidationError: If semester is invalid or out of range.
    """
    if isinstance(semester, bool):
        raise ValidationError(
            field="semester",
            value=semester,
            message="Semester cannot be a boolean value.",
        )

    try:
        sem_int = int(semester)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            field="semester",
            value=semester,
            message=f"Semester must be an integer, got {type(semester).__name__}.",
        ) from exc

    if sem_int < min_semester or sem_int > max_semester:
        raise ValidationError(
            field="semester",
            value=semester,
            message=f"Semester must be between {min_semester} and {max_semester}, got {sem_int}.",
        )
    return sem_int


def validate_cgpa(cgpa: Any, min_cgpa: float = 0.0, max_cgpa: float = 10.0) -> float:
    """Validate Cumulative Grade Point Average (CGPA) on a 0.0 to 10.0 scale.

    Args:
        cgpa: CGPA value (numeric or string representation of float).
        min_cgpa: Minimum allowed CGPA (0.0).
        max_cgpa: Maximum allowed CGPA (10.0).

    Returns:
        Float CGPA rounded to 2 decimal places.

    Raises:
        ValidationError: If CGPA is not numeric or not within 0.0 and 10.0.
    """
    if isinstance(cgpa, bool):
        raise ValidationError(
            field="cgpa",
            value=cgpa,
            message="CGPA cannot be a boolean value.",
        )

    try:
        cgpa_val = float(cgpa)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            field="cgpa",
            value=cgpa,
            message=f"CGPA must be a numeric value between {min_cgpa:.1f} and {max_cgpa:.1f}, got {cgpa!r}.",
        ) from exc

    # Check for NaN / Infinity
    import math

    if math.isnan(cgpa_val) or math.isinf(cgpa_val):
        raise ValidationError(
            field="cgpa",
            value=cgpa,
            message="CGPA must be a finite number.",
        )

    if cgpa_val < min_cgpa or cgpa_val > max_cgpa:
        raise ValidationError(
            field="cgpa",
            value=cgpa,
            message=f"CGPA must be between {min_cgpa:.1f} and {max_cgpa:.1f}, got {cgpa_val:.2f}.",
        )

    return round(cgpa_val, 2)


def validate_student_type(student_type: Any) -> str:
    """Validate student academic level subtype.

    Args:
        student_type: String specifying 'undergraduate' or 'postgraduate'.

    Returns:
        Canonical lowercase subtype string.

    Raises:
        ValidationError: If type is unknown or invalid.
    """
    if not isinstance(student_type, str):
        raise ValidationError(
            field="student_type",
            value=student_type,
            message="Student type must be a string.",
        )
    cleaned = student_type.strip().lower()
    valid_types = {"undergraduate", "postgraduate", "undergrad", "postgrad", "ug", "pg"}
    if cleaned not in valid_types:
        raise ValidationError(
            field="student_type",
            value=student_type,
            message="Student type must be either 'undergraduate' or 'postgraduate'.",
        )
    if cleaned in {"undergraduate", "undergrad", "ug"}:
        return "undergraduate"
    return "postgraduate"
