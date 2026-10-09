"""Unit tests for UniversityRegistrar service and CLI commands."""

from pathlib import Path
import pytest

from university_registrar.exceptions import (
    DuplicateStudentError,
    StudentNotFoundError,
    ValidationError,
)
from university_registrar.main import main
from university_registrar.models import (
    PostgraduateStudent,
    Student,
    UndergraduateStudent,
)
from university_registrar.registrar import UniversityRegistrar


@pytest.fixture
def empty_registrar() -> UniversityRegistrar:
    """Provide a clean in-memory UniversityRegistrar instance."""
    return UniversityRegistrar(storage_path=None, auto_save=False)


@pytest.fixture
def populated_registrar(empty_registrar: UniversityRegistrar) -> UniversityRegistrar:
    """Provide a registrar pre-populated with standard student records."""
    s1 = UndergraduateStudent(
        student_id="UG-001",
        name="Alice Walker",
        email="alice@univ.edu",
        age=20,
        department="Computer Science",
        course="B.S. CS",
        semester=4,
        cgpa=9.2,
        academic_advisor="Dr. Vance",
    )
    s2 = UndergraduateStudent(
        student_id="UG-002",
        name="Bob Martin",
        email="bob@univ.edu",
        age=21,
        department="Computer Science",
        course="B.S. CS",
        semester=6,
        cgpa=8.0,
        academic_advisor="Dr. Vance",
    )
    s3 = PostgraduateStudent(
        student_id="PG-001",
        name="Clara Oswald",
        email="clara@univ.edu",
        age=25,
        department="Physics",
        course="M.S. Physics",
        semester=4,
        cgpa=9.5,
        thesis_supervisor="Prof. Smith",
        research_topic="Quantum Computing",
    )
    empty_registrar.add_student(s1)
    empty_registrar.add_student(s2)
    empty_registrar.add_student(s3)
    return empty_registrar


class TestRegistrarService:
    """Test suite covering the core UniversityRegistrar business logic."""

    def test_add_and_get_student(self, empty_registrar: UniversityRegistrar) -> None:
        student = UndergraduateStudent(
            student_id="UG-100",
            name="Grace Hopper",
            email="grace@univ.edu",
            age=20,
            department="Computer Science",
            course="B.S. CS",
            semester=2,
            cgpa=9.8,
        )
        empty_registrar.add_student(student)

        retrieved = empty_registrar.get_student("UG-100")
        assert retrieved.name == "Grace Hopper"
        assert retrieved.student_id == "UG-100"
        assert "UG-100" in empty_registrar
        assert len(empty_registrar) == 1

    def test_add_duplicate_student_raises_error(self, empty_registrar: UniversityRegistrar) -> None:
        s1 = Student("A", 20, "a@u.edu", "ID-1", "CS", "BS", 1, 8.0)
        s2 = Student("B", 21, "b@u.edu", "ID-1", "EE", "BS", 2, 7.5)
        empty_registrar.add_student(s1)

        with pytest.raises(DuplicateStudentError) as exc:
            empty_registrar.add_student(s2)
        assert exc.value.student_id == "ID-1"

    def test_get_nonexistent_student_raises_error(self, empty_registrar: UniversityRegistrar) -> None:
        with pytest.raises(StudentNotFoundError) as exc:
            empty_registrar.get_student("DOES-NOT-EXIST")
        assert exc.value.student_id == "DOES-NOT-EXIST"

    def test_update_student_success(self, populated_registrar: UniversityRegistrar) -> None:
        updated = populated_registrar.update_student(
            "UG-001",
            {"name": "Alice Cooper", "cgpa": 9.75, "semester": 5},
        )
        assert updated.name == "Alice Cooper"
        assert updated.cgpa == 9.75
        assert updated.semester == 5

        # Verify retrieved reflects changes
        fresh = populated_registrar.get_student("UG-001")
        assert fresh.name == "Alice Cooper"

    def test_update_nonexistent_student_raises_error(self, empty_registrar: UniversityRegistrar) -> None:
        with pytest.raises(StudentNotFoundError):
            empty_registrar.update_student("NONE", {"name": "Test"})

    def test_update_with_duplicate_id_raises_error(self, populated_registrar: UniversityRegistrar) -> None:
        with pytest.raises(DuplicateStudentError):
            populated_registrar.update_student("UG-001", {"student_id": "UG-002"})

    def test_delete_student_success(self, populated_registrar: UniversityRegistrar) -> None:
        assert len(populated_registrar) == 3
        deleted = populated_registrar.delete_student("UG-001")
        assert deleted.student_id == "UG-001"
        assert len(populated_registrar) == 2
        assert "UG-001" not in populated_registrar

        with pytest.raises(StudentNotFoundError):
            populated_registrar.get_student("UG-001")

    def test_delete_nonexistent_student_raises_error(self, empty_registrar: UniversityRegistrar) -> None:
        with pytest.raises(StudentNotFoundError):
            empty_registrar.delete_student("MISSING-ID")

    def test_search_students(self, populated_registrar: UniversityRegistrar) -> None:
        # Search by name
        res = populated_registrar.search_students("walker")
        assert len(res) == 1
        assert res[0].student_id == "UG-001"

        # Search by department
        res_cs = populated_registrar.search_students("computer")
        assert len(res_cs) == 2

        # Search by ID
        res_id = populated_registrar.search_students("PG-001")
        assert len(res_id) == 1

        # Search with no match
        assert populated_registrar.search_students("nonexistent query") == []
        assert populated_registrar.search_students("") == []

    def test_filter_by_department(self, populated_registrar: UniversityRegistrar) -> None:
        cs = populated_registrar.filter_by_department("Computer Science")
        assert len(cs) == 2
        physics = populated_registrar.filter_by_department("Physics")
        assert len(physics) == 1
        assert physics[0].student_id == "PG-001"
        assert populated_registrar.filter_by_department("Biology") == []

    def test_filter_by_type(self, populated_registrar: UniversityRegistrar) -> None:
        ugs = populated_registrar.filter_by_type("undergraduate")
        assert len(ugs) == 2
        pgs = populated_registrar.filter_by_type("postgraduate")
        assert len(pgs) == 1

    def test_statistics_calculation(self, populated_registrar: UniversityRegistrar) -> None:
        stats = populated_registrar.get_statistics()
        assert stats["total_students"] == 3
        assert stats["undergraduate_count"] == 2
        assert stats["postgraduate_count"] == 1
        # CGPAs: 9.2, 8.0, 9.5 -> avg = (26.7) / 3 = 8.90
        assert stats["average_cgpa"] == 8.90
        assert stats["highest_cgpa"] == 9.5
        assert stats["lowest_cgpa"] == 8.0
        assert stats["department_counts"]["Computer Science"] == 2
        assert stats["department_counts"]["Physics"] == 1
        assert stats["dean_list_count"] == 1  # Alice has 9.2 (>= 8.5), Bob has 8.0 (< 8.5)
        assert stats["defense_eligible_count"] == 1  # Clara is sem 4, cgpa 9.5, valid research

    def test_statistics_empty_registrar(self, empty_registrar: UniversityRegistrar) -> None:
        stats = empty_registrar.get_statistics()
        assert stats["total_students"] == 0
        assert stats["average_cgpa"] == 0.0
        assert stats["department_counts"] == {}

    def test_export_and_import_round_trip(self, populated_registrar: UniversityRegistrar, tmp_path: Path) -> None:
        export_file = tmp_path / "backup.json"
        exported_count = populated_registrar.export_students(export_file)
        assert exported_count == 3
        assert export_file.exists()

        new_registrar = UniversityRegistrar(storage_path=export_file)
        assert len(new_registrar) == 3
        assert new_registrar.get_student("UG-001").name == "Alice Walker"

    def test_import_failure_rolls_back_without_partial_changes(
        self,
        populated_registrar: UniversityRegistrar,
        tmp_path: Path,
    ) -> None:
        # Create a file with 1 valid and 1 invalid record
        bad_file = tmp_path / "corrupt_batch.json"
        bad_file.write_text(
            """
            {
              "students": [
                {
                  "name": "New Valid Student",
                  "age": 20,
                  "email": "valid@u.edu",
                  "student_id": "NEW-001",
                  "department": "CS",
                  "course": "BS",
                  "semester": 1,
                  "cgpa": 8.0
                },
                {
                  "name": "Invalid Student",
                  "age": 20,
                  "email": "invalid@u.edu",
                  "student_id": "NEW-002",
                  "department": "CS",
                  "course": "BS",
                  "semester": 1,
                  "cgpa": 99.0
                }
              ]
            }
            """,
            encoding="utf-8",
        )

        initial_count = len(populated_registrar)
        with pytest.raises(ValidationError):
            populated_registrar.import_students(bad_file)

        # Ensure state was not modified (all-or-nothing transactional integrity)
        assert len(populated_registrar) == initial_count
        assert "NEW-001" not in populated_registrar

    def test_cli_help(self, capsys: pytest.CaptureFixture) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "university-registrar" in captured.out
        assert "add" in captured.out
        assert "list" in captured.out

    def test_cli_add_and_list_flow(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        db = tmp_path / "cli_test.json"
        # CLI add student
        exit_code = main([
            "-d", str(db),
            "add",
            "--id", "UG-999",
            "--name", "Ada Lovelace",
            "--email", "ada@computing.edu",
            "--age", "22",
            "--dept", "Mathematics",
            "--course", "B.S. Math",
            "--semester", "3",
            "--cgpa", "9.9",
            "--type", "undergraduate",
        ])
        assert exit_code == 0

        # CLI list
        exit_code = main(["-d", str(db), "list"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Ada Lovelace" in captured.out
        assert "UG-999" in captured.out

        # CLI stats
        exit_code = main(["-d", str(db), "stats"])
        assert exit_code == 0
        captured_stats = capsys.readouterr()
        assert "Total Registered Students : 1" in captured_stats.out
