"""University Registrar - Object-Oriented Data Management and Exception Handling System.

Package exposing core models, custom exceptions, validation functions,
persistence utilities, and the UniversityRegistrar manager service.
"""

from university_registrar.exceptions import (
    DuplicateStudentError,
    RegistrarError,
    StudentNotFoundError,
    StorageError,
    UnsupportedFormatError,
    ValidationError,
)
from university_registrar.models import (
    Person,
    PostgraduateStudent,
    Student,
    UndergraduateStudent,
)
from university_registrar.registrar import UniversityRegistrar
from university_registrar.storage import (
    export_students_csv,
    import_students_csv,
    load_students,
    load_students_json,
    save_students,
    save_students_json,
)
from university_registrar.validators import (
    validate_age,
    validate_cgpa,
    validate_course,
    validate_department,
    validate_email,
    validate_name,
    validate_semester,
    validate_student_id,
    validate_student_type,
)

__version__ = "1.0.0"

__all__ = [
    # Models
    "Person",
    "Student",
    "UndergraduateStudent",
    "PostgraduateStudent",
    # Registrar Service
    "UniversityRegistrar",
    # Exceptions
    "RegistrarError",
    "ValidationError",
    "DuplicateStudentError",
    "StudentNotFoundError",
    "StorageError",
    "UnsupportedFormatError",
    # Storage
    "save_students_json",
    "load_students_json",
    "export_students_csv",
    "import_students_csv",
    "save_students",
    "load_students",
    # Validators
    "validate_name",
    "validate_email",
    "validate_age",
    "validate_student_id",
    "validate_department",
    "validate_course",
    "validate_semester",
    "validate_cgpa",
    "validate_student_type",
]
