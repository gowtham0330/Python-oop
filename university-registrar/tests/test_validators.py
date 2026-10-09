"""Unit tests for input validation logic."""

import pytest
from university_registrar.exceptions import ValidationError
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


class TestValidators:
    """Test suite covering all domain validation functions."""

    def test_validate_name_success(self) -> None:
        assert validate_name("  Ada Lovelace  ") == "Ada Lovelace"
        assert validate_name("Jean-Luc Picard") == "Jean-Luc Picard"

    @pytest.mark.parametrize("invalid_name", ["", "   ", 1234, None, "123456", "!!!", "@#$"])
    def test_validate_name_failure(self, invalid_name) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_name(invalid_name)
        assert exc_info.value.field == "name"

    def test_validate_email_success(self) -> None:
        assert validate_email("Student.One@University.EDU ") == "student.one@university.edu"
        assert validate_email("dev+tag@domain.co.uk") == "dev+tag@domain.co.uk"

    @pytest.mark.parametrize(
        "invalid_email",
        ["", "plainaddress", "@missinguser.com", "user@", "user@domain", 1234, None]
    )
    def test_validate_email_failure(self, invalid_email) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_email(invalid_email)
        assert exc_info.value.field == "email"

    def test_validate_age_success(self) -> None:
        assert validate_age(20) == 20
        assert validate_age("25") == 25
        assert validate_age(16) == 16
        assert validate_age(100) == 100

    @pytest.mark.parametrize("invalid_age", [15, 101, -5, "not_a_num", True, False, None, 14.5])
    def test_validate_age_failure(self, invalid_age) -> None:
        # Note: 14.5 as string will raise ValueError in int(), 14.5 float will convert or fail if not handled
        with pytest.raises(ValidationError) as exc_info:
            validate_age(invalid_age)
        assert exc_info.value.field == "age"

    def test_validate_student_id_success(self) -> None:
        assert validate_student_id("  UG-2024-001 ") == "UG-2024-001"

    @pytest.mark.parametrize("invalid_id", ["", "   ", None, 12345])
    def test_validate_student_id_failure(self, invalid_id) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_student_id(invalid_id)
        assert exc_info.value.field == "student_id"

    def test_validate_department_and_course_success(self) -> None:
        assert validate_department(" Computer Science ") == "Computer Science"
        assert validate_course(" B.Tech CS ") == "B.Tech CS"

    def test_validate_department_and_course_failure(self) -> None:
        with pytest.raises(ValidationError):
            validate_department("   ")
        with pytest.raises(ValidationError):
            validate_course("")

    def test_validate_semester_success(self) -> None:
        assert validate_semester(1) == 1
        assert validate_semester("8") == 8
        assert validate_semester(12) == 12

    @pytest.mark.parametrize("invalid_semester", [0, 13, -1, "third", True, None])
    def test_validate_semester_failure(self, invalid_semester) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_semester(invalid_semester)
        assert exc_info.value.field == "semester"

    def test_validate_cgpa_success(self) -> None:
        assert validate_cgpa(9.5) == 9.5
        assert validate_cgpa("8.75") == 8.75
        assert validate_cgpa(0.0) == 0.0
        assert validate_cgpa(10.0) == 10.0

    @pytest.mark.parametrize("invalid_cgpa", [-0.1, 10.1, "excellent", "fail", True, None, float("nan"), float("inf")])
    def test_validate_cgpa_failure(self, invalid_cgpa) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_cgpa(invalid_cgpa)
        assert exc_info.value.field == "cgpa"
        assert "CGPA" in str(exc_info.value)

    def test_validate_student_type(self) -> None:
        assert validate_student_type("undergraduate") == "undergraduate"
        assert validate_student_type("UG") == "undergraduate"
        assert validate_student_type("postgraduate") == "postgraduate"
        assert validate_student_type("PG") == "postgraduate"

        with pytest.raises(ValidationError) as exc_info:
            validate_student_type("alumni")
        assert exc_info.value.field == "student_type"
