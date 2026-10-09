"""Unit tests for Person and Student class inheritance hierarchy."""

import pytest
from university_registrar.exceptions import ValidationError
from university_registrar.models import (
    Person,
    PostgraduateStudent,
    Student,
    UndergraduateStudent,
)


class TestModels:
    """Test suite covering object-oriented models and inheritance behaviors."""

    def test_create_valid_person(self) -> None:
        person = Person(name="Alice Smith", age=22, email="alice@university.edu")
        assert person.name == "Alice Smith"
        assert person.age == 22
        assert person.email == "alice@university.edu"
        data = person.to_dict()
        assert data == {"name": "Alice Smith", "age": 22, "email": "alice@university.edu"}

        recreated = Person.from_dict(data)
        assert recreated.name == person.name
        assert recreated.age == person.age

    def test_person_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            Person.from_dict({"name": "Bob", "age": 25})  # missing email
        with pytest.raises(ValidationError):
            Person.from_dict("not-a-dict")  # type mismatch

    def test_create_valid_student(self) -> None:
        student = Student(
            name="Bob Jones",
            age=21,
            email="bob@university.edu",
            student_id="STU-001",
            department="Computer Science",
            course="B.S. Software Eng",
            semester=5,
            cgpa=7.5,
        )
        assert isinstance(student, Person)
        assert student.student_id == "STU-001"
        assert student.is_passing is True

        d = student.to_dict()
        assert d["student_id"] == "STU-001"
        assert d["cgpa"] == 7.5
        assert d["name"] == "Bob Jones"

    def test_undergraduate_student_properties(self) -> None:
        ug = UndergraduateStudent(
            name="Charlie Brown",
            age=20,
            email="charlie@university.edu",
            student_id="UG-101",
            department="Physics",
            course="B.S. Physics",
            semester=4,
            cgpa=9.1,
            academic_advisor="Dr. Lin",
            internship_status="Completed",
        )
        assert isinstance(ug, Student)
        assert isinstance(ug, Person)
        assert ug.academic_standing == "Dean's List"
        assert ug.student_type == "undergraduate"

        # Check serialization contains undergraduate details
        data = ug.to_dict()
        assert data["academic_advisor"] == "Dr. Lin"
        assert data["academic_standing"] == "Dean's List"

        # Factory deserialization resolves into UndergraduateStudent
        deserialized = Student.from_dict(data)
        assert isinstance(deserialized, UndergraduateStudent)
        assert deserialized.academic_standing == "Dean's List"

    def test_undergraduate_academic_standings(self) -> None:
        # Dean's list >= 8.5
        ug1 = UndergraduateStudent("A", 20, "a@u.edu", "U1", "CS", "BS", 1, 8.5)
        assert ug1.academic_standing == "Dean's List"

        # Good standing >= 5.0
        ug2 = UndergraduateStudent("B", 20, "b@u.edu", "U2", "CS", "BS", 1, 6.5)
        assert ug2.academic_standing == "Good Standing"

        # Academic warning < 5.0
        ug3 = UndergraduateStudent("C", 20, "c@u.edu", "U3", "CS", "BS", 1, 4.8)
        assert ug3.academic_standing == "Academic Warning"

    def test_undergraduate_semester_boundary(self) -> None:
        # Valid up to semester 8
        UndergraduateStudent("A", 20, "a@u.edu", "U1", "CS", "BS", 8, 8.0)
        # Exceeding 8 should fail
        with pytest.raises(ValidationError) as exc:
            UndergraduateStudent("A", 20, "a@u.edu", "U1", "CS", "BS", 9, 8.0)
        assert exc.value.field == "semester"

    def test_postgraduate_student_properties(self) -> None:
        pg = PostgraduateStudent(
            name="Diana Prince",
            age=26,
            email="diana@university.edu",
            student_id="PG-201",
            department="Chemistry",
            course="M.S. Organic Chemistry",
            semester=4,
            cgpa=8.2,
            thesis_supervisor="Prof. Wayne",
            research_topic="Catalytic Synthetics",
        )
        assert isinstance(pg, Student)
        assert isinstance(pg, Person)
        assert pg.student_type == "postgraduate"
        assert pg.defense_eligible is True

        data = pg.to_dict()
        assert data["thesis_supervisor"] == "Prof. Wayne"
        assert data["research_topic"] == "Catalytic Synthetics"

        # Factory deserialization resolves into PostgraduateStudent
        deserialized = Student.from_dict(data)
        assert isinstance(deserialized, PostgraduateStudent)
        assert deserialized.research_topic == "Catalytic Synthetics"

    def test_postgraduate_defense_eligibility(self) -> None:
        # Semester < 3 -> not eligible
        pg1 = PostgraduateStudent("A", 25, "a@u.edu", "P1", "CH", "MS", 2, 8.5, research_topic="Nano")
        assert pg1.defense_eligible is False

        # CGPA < 7.0 -> not eligible
        pg2 = PostgraduateStudent("B", 25, "b@u.edu", "P2", "CH", "MS", 4, 6.8, research_topic="Nano")
        assert pg2.defense_eligible is False

        # TBD research topic -> not eligible
        pg3 = PostgraduateStudent("C", 25, "c@u.edu", "P3", "CH", "MS", 4, 8.0, research_topic="TBD")
        assert pg3.defense_eligible is False

        # Semester >= 3, CGPA >= 7.0, valid topic -> eligible
        pg4 = PostgraduateStudent("D", 25, "d@u.edu", "P4", "CH", "MS", 3, 7.0, research_topic="Nano")
        assert pg4.defense_eligible is True

    def test_postgraduate_semester_boundary(self) -> None:
        # Postgraduate allowed max 6 semesters
        PostgraduateStudent("A", 25, "a@u.edu", "P1", "CH", "MS", 6, 8.0)
        with pytest.raises(ValidationError) as exc:
            PostgraduateStudent("A", 25, "a@u.edu", "P1", "CH", "MS", 7, 8.0)
        assert exc.value.field == "semester"

    def test_student_equality_and_hashing(self) -> None:
        s1 = Student("A", 20, "a@u.edu", "ID-100", "CS", "BS", 1, 8.0)
        s2 = Student("B", 22, "b@u.edu", "ID-100", "EE", "BS", 2, 7.0)
        s3 = Student("C", 20, "c@u.edu", "ID-200", "CS", "BS", 1, 8.0)

        assert s1 == s2  # Same ID implies same identity
        assert s1 != s3
        assert hash(s1) == hash(s2)
        assert len({s1, s2, s3}) == 2
