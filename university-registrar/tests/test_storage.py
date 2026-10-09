"""Unit tests for JSON and CSV file storage and persistence."""

from pathlib import Path
from unittest.mock import patch
import pytest

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
from university_registrar.storage import (
    export_students_csv,
    import_students_csv,
    load_students,
    load_students_json,
    save_students,
    save_students_json,
)


@pytest.fixture
def sample_student_instances() -> list[Student]:
    """Provide a mixed list of undergraduate and postgraduate students."""
    return [
        UndergraduateStudent(
            student_id="UG-001",
            name="Alice Walker",
            email="alice@univ.edu",
            age=20,
            department="Computer Science",
            course="B.S. CS",
            semester=4,
            cgpa=9.2,
            academic_advisor="Dr. Vance",
            internship_status="Completed",
        ),
        PostgraduateStudent(
            student_id="PG-001",
            name="Bob Ross",
            email="bob@univ.edu",
            age=26,
            department="Fine Arts",
            course="M.F.A Painting",
            semester=3,
            cgpa=8.5,
            research_topic="Color Theory",
            thesis_supervisor="Prof. Monet",
        ),
    ]


class TestStorage:
    """Test suite covering serialization, atomic I/O, and error resilience."""

    def test_json_round_trip(self, tmp_path: Path, sample_student_instances: list[Student]) -> None:
        file_path = tmp_path / "students.json"
        save_students_json(file_path, sample_student_instances)

        assert file_path.exists()
        loaded = load_students_json(file_path)

        assert len(loaded) == 2
        assert isinstance(loaded[0], UndergraduateStudent)
        assert isinstance(loaded[1], PostgraduateStudent)
        assert loaded[0].student_id == "UG-001"
        assert loaded[0].academic_advisor == "Dr. Vance"
        assert loaded[1].research_topic == "Color Theory"

    def test_csv_round_trip(self, tmp_path: Path, sample_student_instances: list[Student]) -> None:
        file_path = tmp_path / "students.csv"
        export_students_csv(file_path, sample_student_instances)

        assert file_path.exists()
        loaded = import_students_csv(file_path)

        assert len(loaded) == 2
        assert isinstance(loaded[0], UndergraduateStudent)
        assert isinstance(loaded[1], PostgraduateStudent)
        assert loaded[0].name == "Alice Walker"
        assert loaded[0].academic_advisor == "Dr. Vance"
        assert loaded[1].thesis_supervisor == "Prof. Monet"

    def test_load_nonexistent_json_raises_storage_error(self, tmp_path: Path) -> None:
        missing_file = tmp_path / "not_there.json"
        with pytest.raises(StorageError) as exc_info:
            load_students_json(missing_file)
        assert "not found" in str(exc_info.value).lower()

    def test_load_nonexistent_csv_raises_storage_error(self, tmp_path: Path) -> None:
        missing_file = tmp_path / "not_there.csv"
        with pytest.raises(StorageError) as exc_info:
            import_students_csv(missing_file)
        assert "not found" in str(exc_info.value).lower()

    def test_load_malformed_json(self, tmp_path: Path) -> None:
        bad_json = tmp_path / "corrupt.json"
        bad_json.write_text("{ unquoted_key: 'value' broken }", encoding="utf-8")
        with pytest.raises(StorageError) as exc_info:
            load_students_json(bad_json)
        assert "malformed" in str(exc_info.value).lower()

    def test_load_json_invalid_structure(self, tmp_path: Path) -> None:
        bad_json = tmp_path / "not_list.json"
        bad_json.write_text('{"students": "not-a-list"}', encoding="utf-8")
        with pytest.raises(StorageError):
            load_students_json(bad_json)

    def test_load_json_invalid_student_record(self, tmp_path: Path) -> None:
        bad_json = tmp_path / "invalid_record.json"
        bad_json.write_text('{"students": [{"name": "Only Name"}]}', encoding="utf-8")
        with pytest.raises(ValidationError):
            load_students_json(bad_json)

    def test_csv_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("", encoding="utf-8")
        assert import_students_csv(empty_csv) == []

    def test_csv_missing_required_headers(self, tmp_path: Path) -> None:
        bad_csv = tmp_path / "missing_header.csv"
        bad_csv.write_text("student_id,name\n1,Alice\n", encoding="utf-8")
        with pytest.raises(StorageError) as exc_info:
            import_students_csv(bad_csv)
        assert "missing required columns" in str(exc_info.value).lower()

    def test_csv_invalid_numeric_value(self, tmp_path: Path) -> None:
        bad_csv = tmp_path / "bad_data.csv"
        content = (
            "student_id,name,email,age,department,course,semester,cgpa,student_type\n"
            "UG-1,Alice,alice@u.edu,twenty,CS,BS,1,8.0,undergraduate\n"
        )
        bad_csv.write_text(content, encoding="utf-8")
        with pytest.raises(ValidationError) as exc_info:
            import_students_csv(bad_csv)
        assert exc_info.value.field == "age"

    def test_generic_save_and_load_routing(self, tmp_path: Path, sample_student_instances: list[Student]) -> None:
        j_path = tmp_path / "out.json"
        c_path = tmp_path / "out.csv"

        save_students(j_path, sample_student_instances)
        save_students(c_path, sample_student_instances)

        assert len(load_students(j_path)) == 2
        assert len(load_students(c_path)) == 2

    def test_unsupported_file_extension(self, tmp_path: Path, sample_student_instances: list[Student]) -> None:
        xml_path = tmp_path / "out.xml"
        with pytest.raises(UnsupportedFormatError) as exc_info:
            save_students(xml_path, sample_student_instances)
        assert ".xml" in str(exc_info.value)

        with pytest.raises(UnsupportedFormatError):
            load_students(xml_path)

    def test_storage_permission_error_mocked(self, tmp_path: Path, sample_student_instances: list[Student]) -> None:
        target = tmp_path / "locked.json"
        with patch("tempfile.mkstemp", side_effect=PermissionError("Permission denied")):
            with pytest.raises(StorageError) as exc_info:
                save_students_json(target, sample_student_instances)
            assert "Permission denied" in str(exc_info.value) or "Failed to write" in str(exc_info.value)

    def test_atomic_write_creates_parent_directories(self, tmp_path: Path, sample_student_instances: list[Student]) -> None:
        nested_file = tmp_path / "deep" / "nested" / "dir" / "students.json"
        save_students_json(nested_file, sample_student_instances)
        assert nested_file.exists()
        assert len(load_students_json(nested_file)) == 2
