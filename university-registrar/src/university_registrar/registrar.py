"""Core business logic service for the University Registrar system.

Manages student records, enforces uniqueness, calculates statistics, and orchestrates
atomic persistence to JSON and CSV.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from university_registrar.exceptions import (
    DuplicateStudentError,
    StudentNotFoundError,
    ValidationError,
)
from university_registrar.models import (
    PostgraduateStudent,
    Student,
    UndergraduateStudent,
)
from university_registrar.storage import load_students, save_students
from university_registrar.validators import validate_student_id


class UniversityRegistrar:
    """Central service managing university student records and academic operations.

    Attributes:
        storage_path: Optional path for automated file persistence.
        auto_save: When True, changes are automatically written to storage_path.
    """

    def __init__(
        self,
        storage_path: Optional[Union[str, Path]] = None,
        auto_save: bool = True,
    ) -> None:
        """Initialize the registrar.

        Args:
            storage_path: Path to persistent storage (.json or .csv).
            auto_save: Whether to automatically save on mutations.
        """
        self._students: Dict[str, Student] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        self.auto_save = auto_save and self.storage_path is not None

        if self.storage_path and self.storage_path.is_file():
            self._load_from_storage()

    def _load_from_storage(self) -> None:
        """Load records from the configured storage path."""
        if not self.storage_path:
            return
        loaded = load_students(self.storage_path)
        for s in loaded:
            self._students[s.student_id] = s

    def _persist(self) -> None:
        """Write current records to configured storage path if auto_save is enabled."""
        if self.auto_save and self.storage_path:
            save_students(self.storage_path, list(self._students.values()))

    def add_student(self, student: Student) -> Student:
        """Register a new student.

        Args:
            student: Student instance to add.

        Returns:
            The added Student.

        Raises:
            ValidationError: If student is not a valid Student instance.
            DuplicateStudentError: If a student with the same ID already exists.
        """
        if not isinstance(student, Student):
            raise ValidationError(
                field="student",
                value=student,
                message=f"Expected Student instance, got {type(student).__name__}.",
            )

        sid = student.student_id
        if sid in self._students:
            raise DuplicateStudentError(sid)

        self._students[sid] = student
        self._persist()
        return student

    def get_student(self, student_id: str) -> Student:
        """Retrieve a student by identifier.

        Args:
            student_id: Unique student identifier.

        Returns:
            The found Student.

        Raises:
            StudentNotFoundError: If student is not registered.
        """
        sid = validate_student_id(student_id)
        if sid not in self._students:
            raise StudentNotFoundError(sid)
        return self._students[sid]

    def update_student(
        self,
        student_id: str,
        updated_data: Dict[str, Any],
    ) -> Student:
        """Update fields of an existing student.

        All updates are validated before the record is modified.

        Args:
            student_id: Existing student ID.
            updated_data: Dictionary of fields to update.

        Returns:
            The updated Student instance.

        Raises:
            StudentNotFoundError: If student does not exist.
            ValidationError: If updated values are invalid.
            DuplicateStudentError: If attempting to rename to a conflicting ID.
        """
        existing = self.get_student(student_id)

        if not isinstance(updated_data, dict):
            raise ValidationError(
                field="updated_data",
                value=updated_data,
                message="Updates must be provided as a dictionary.",
            )

        new_id = updated_data.get("student_id")
        if new_id and new_id != student_id:
            cleaned_new_id = validate_student_id(new_id)
            if cleaned_new_id in self._students:
                raise DuplicateStudentError(cleaned_new_id)

        # Merge existing dictionary with updates
        merged = existing.to_dict()
        merged.update(updated_data)

        # Re-instantiate through polymorphic factory
        updated_student = Student.from_dict(merged)

        # Remove old key if ID changed
        if student_id != updated_student.student_id:
            del self._students[student_id]

        self._students[updated_student.student_id] = updated_student
        self._persist()
        return updated_student

    def delete_student(self, student_id: str) -> Student:
        """Remove a student from the registrar.

        Args:
            student_id: Identifier of the student to remove.

        Returns:
            The removed Student instance.

        Raises:
            StudentNotFoundError: If student does not exist.
        """
        student = self.get_student(student_id)
        del self._students[student.student_id]
        self._persist()
        return student

    def list_students(
        self,
        sort_by: Optional[str] = "id",
    ) -> List[Student]:
        """List all registered students.

        Args:
            sort_by: Field to sort results by ('id', 'name', 'department', 'cgpa').

        Returns:
            List of student instances.
        """
        students = list(self._students.values())

        if sort_by == "name":
            students.sort(key=lambda s: s.name.lower())
        elif sort_by == "department":
            students.sort(key=lambda s: (s.department.lower(), s.name.lower()))
        elif sort_by == "cgpa":
            students.sort(key=lambda s: s.cgpa, reverse=True)
        else:  # default by ID
            students.sort(key=lambda s: s.student_id)

        return students

    def search_students(self, query: str) -> List[Student]:
        """Search students with case-insensitive matching across multiple fields.

        Matches query against student_id, name, department, course, and email.

        Args:
            query: Search keyword.

        Returns:
            List of matching students.
        """
        if not isinstance(query, str) or not query.strip():
            return []

        q = query.strip().lower()
        results: List[Student] = []

        for student in self._students.values():
            student_dict = student.to_dict()
            searchable_text = " ".join(str(v) for v in student_dict.values()).lower()
            if q in searchable_text:
                results.append(student)

        results.sort(key=lambda s: s.student_id)
        return results

    def filter_by_department(self, department: str) -> List[Student]:
        """Filter students by department name (case-insensitive).

        Args:
            department: Department name.

        Returns:
            List of students in the matching department.
        """
        d = department.strip().lower()
        results = [
            s for s in self._students.values()
            if s.department.strip().lower() == d
        ]
        results.sort(key=lambda s: s.name.lower())
        return results

    def filter_by_type(self, student_type: str) -> List[Student]:
        """Filter students by subtype ('undergraduate' or 'postgraduate').

        Args:
            student_type: Target subtype string.

        Returns:
            Filtered list of students.
        """
        target = student_type.strip().lower()
        if target in {"undergraduate", "undergrad", "ug"}:
            return [s for s in self._students.values() if isinstance(s, UndergraduateStudent)]
        elif target in {"postgraduate", "postgrad", "pg"}:
            return [s for s in self._students.values() if isinstance(s, PostgraduateStudent)]
        return [s for s in self._students.values() if s.student_type.lower() == target]

    def export_students(self, file_path: Union[str, Path]) -> int:
        """Export all registered students to a JSON or CSV file.

        Args:
            file_path: Destination file path.

        Returns:
            Total number of exported students.
        """
        students = self.list_students(sort_by="id")
        save_students(file_path, students)
        return len(students)

    def import_students(
        self,
        file_path: Union[str, Path],
        merge: bool = True,
    ) -> int:
        """Import students from a JSON or CSV file.

        Enforces all-or-nothing transactional integrity: all imported records
        are validated before modifying the registrar state. If any record fails
        validation or produces an invalid duplicate, no records are added.

        Args:
            file_path: Path to source file.
            merge: If True, merges with existing students. If False, replaces all.

        Returns:
            Number of newly imported records.

        Raises:
            StorageError: If file loading fails.
            ValidationError: If record validation fails.
            DuplicateStudentError: If duplicate IDs are encountered within the import batch.
        """
        incoming = load_students(file_path)

        # Validate batch uniqueness within incoming data
        seen_incoming_ids = set()
        for s in incoming:
            if s.student_id in seen_incoming_ids:
                raise DuplicateStudentError(
                    f"Duplicate ID '{s.student_id}' found within the import batch."
                )
            seen_incoming_ids.add(s.student_id)

        # Prepare new state
        new_state = dict(self._students) if merge else {}

        # If merging, check conflicts or overwrite
        for s in incoming:
            new_state[s.student_id] = s

        # Commit state transactionally
        self._students = new_state
        self._persist()
        return len(incoming)

    def get_statistics(self) -> Dict[str, Any]:
        """Compute comprehensive registrar analytics.

        Returns:
            Dictionary containing metrics, department breakdowns, and honors counts.
        """
        students = list(self._students.values())
        total = len(students)

        if total == 0:
            return {
                "total_students": 0,
                "undergraduate_count": 0,
                "postgraduate_count": 0,
                "general_count": 0,
                "average_cgpa": 0.0,
                "highest_cgpa": 0.0,
                "lowest_cgpa": 0.0,
                "department_counts": {},
                "cgpa_distribution": {
                    "9.0 - 10.0 (Exceptional)": 0,
                    "8.0 - 8.9 (Very Good)": 0,
                    "7.0 - 7.9 (Good)": 0,
                    "5.0 - 6.9 (Satisfactory)": 0,
                    "< 5.0 (At Risk)": 0,
                },
                "dean_list_count": 0,
                "defense_eligible_count": 0,
            }

        ug_count = sum(1 for s in students if isinstance(s, UndergraduateStudent))
        pg_count = sum(1 for s in students if isinstance(s, PostgraduateStudent))
        gen_count = total - ug_count - pg_count

        cgpas = [s.cgpa for s in students]
        avg_cgpa = round(sum(cgpas) / total, 2)
        highest_cgpa = max(cgpas)
        lowest_cgpa = min(cgpas)

        # Department breakdown
        dept_counts: Dict[str, int] = {}
        for s in students:
            dept = s.department
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        # CGPA distribution
        dist = {
            "9.0 - 10.0 (Exceptional)": sum(1 for c in cgpas if c >= 9.0),
            "8.0 - 8.9 (Very Good)": sum(1 for c in cgpas if 8.0 <= c < 9.0),
            "7.0 - 7.9 (Good)": sum(1 for c in cgpas if 7.0 <= c < 8.0),
            "5.0 - 6.9 (Satisfactory)": sum(1 for c in cgpas if 5.0 <= c < 7.0),
            "< 5.0 (At Risk)": sum(1 for c in cgpas if c < 5.0),
        }

        dean_list = sum(
            1 for s in students
            if isinstance(s, UndergraduateStudent) and s.academic_standing == "Dean's List"
        )

        defense_eligible = sum(
            1 for s in students
            if isinstance(s, PostgraduateStudent) and s.defense_eligible
        )

        return {
            "total_students": total,
            "undergraduate_count": ug_count,
            "postgraduate_count": pg_count,
            "general_count": gen_count,
            "average_cgpa": avg_cgpa,
            "highest_cgpa": highest_cgpa,
            "lowest_cgpa": lowest_cgpa,
            "department_counts": dept_counts,
            "cgpa_distribution": dist,
            "dean_list_count": dean_list,
            "defense_eligible_count": defense_eligible,
        }

    def __len__(self) -> int:
        return len(self._students)

    def __contains__(self, student_id: str) -> bool:
        return student_id in self._students
