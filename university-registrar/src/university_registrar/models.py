"""Object-oriented domain models for the University Registrar system.

Implements an inheritance hierarchy:
    Person -> Student -> UndergraduateStudent, PostgraduateStudent
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional, Type

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


@dataclass
class Person:
    """Base class representing a person associated with the university.

    Attributes:
        name: Full legal name.
        age: Age in years.
        email: Contact email address.
    """

    name: str
    age: int
    email: str

    def __post_init__(self) -> None:
        """Validate base person attributes upon instantiation."""
        self.name = validate_name(self.name)
        self.age = validate_age(self.age)
        self.email = validate_email(self.email)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the person instance into a dictionary.

        Returns:
            Dict containing name, age, and email.
        """
        return {
            "name": self.name,
            "age": self.age,
            "email": self.email,
        }

    @classmethod
    def from_dict(cls: Type[Person], data: Dict[str, Any]) -> Person:
        """Construct a Person from dictionary data.

        Args:
            data: Dictionary containing person attributes.

        Returns:
            New Person instance.

        Raises:
            ValidationError: If required fields are missing or invalid.
        """
        if not isinstance(data, dict):
            raise ValidationError(
                field="root",
                value=data,
                message=f"Expected dictionary record, got {type(data).__name__}.",
            )

        for required in ("name", "age", "email"):
            if required not in data:
                raise ValidationError(
                    field=required,
                    value=None,
                    message=f"Missing required person field '{required}'.",
                )

        return cls(
            name=data["name"],
            age=data["age"],
            email=data["email"],
        )


@dataclass
class Student(Person):
    """Represents a general university student.

    Inherits base personal details from Person and introduces academic records.

    Attributes:
        student_id: Unique university student identification code.
        department: Academic department name.
        course: Program of study / course title.
        semester: Current enrolled semester number (1 to 12).
        cgpa: Cumulative Grade Point Average (0.00 to 10.00).
        student_type: Distinguishes 'undergraduate' or 'postgraduate'.
    """

    student_id: str
    department: str
    course: str
    semester: int
    cgpa: float
    student_type: str = "general"

    # Default semester boundaries for general students
    MIN_SEMESTER: int = 1
    MAX_SEMESTER: int = 12

    def __post_init__(self) -> None:
        """Validate both inherited person fields and academic fields."""
        super().__post_init__()
        self.student_id = validate_student_id(self.student_id)
        self.department = validate_department(self.department)
        self.course = validate_course(self.course)
        self.semester = validate_semester(
            self.semester,
            min_semester=self.MIN_SEMESTER,
            max_semester=self.MAX_SEMESTER,
        )
        self.cgpa = validate_cgpa(self.cgpa)

    @property
    def is_passing(self) -> bool:
        """Check if the student has a passing cumulative GPA (>= 4.0)."""
        return self.cgpa >= 4.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize student to dictionary representation."""
        base = super().to_dict()
        base.update(
            {
                "student_id": self.student_id,
                "department": self.department,
                "course": self.course,
                "semester": self.semester,
                "cgpa": self.cgpa,
                "student_type": self.student_type,
            }
        )
        return base

    @classmethod
    def from_dict(cls: Type[Student], data: Dict[str, Any]) -> Student:
        """Construct the appropriate Student subtype from dictionary data.

        If student_type is 'undergraduate' or 'postgraduate', instantiates the
        respective subclass.

        Args:
            data: Dictionary representation of student.

        Returns:
            Instantiated Student, UndergraduateStudent, or PostgraduateStudent.
        """
        if not isinstance(data, dict):
            raise ValidationError(
                field="root",
                value=data,
                message=f"Expected student dictionary, got {type(data).__name__}.",
            )

        required_fields = (
            "name",
            "age",
            "email",
            "student_id",
            "department",
            "course",
            "semester",
            "cgpa",
        )
        for req in required_fields:
            if req not in data:
                raise ValidationError(
                    field=req,
                    value=None,
                    message=f"Missing required student field '{req}'.",
                )

        stype = data.get("student_type", "").lower()
        if stype in {"undergraduate", "undergrad", "ug"}:
            return UndergraduateStudent(
                name=data["name"],
                age=data["age"],
                email=data["email"],
                student_id=data["student_id"],
                department=data["department"],
                course=data["course"],
                semester=data["semester"],
                cgpa=data["cgpa"],
                academic_advisor=data.get("academic_advisor", "General Advisor"),
                internship_status=data.get("internship_status", "Not Started"),
            )
        elif stype in {"postgraduate", "postgrad", "pg"}:
            return PostgraduateStudent(
                name=data["name"],
                age=data["age"],
                email=data["email"],
                student_id=data["student_id"],
                department=data["department"],
                course=data["course"],
                semester=data["semester"],
                cgpa=data["cgpa"],
                research_topic=data.get("research_topic", "General Research"),
                thesis_supervisor=data.get("thesis_supervisor", "Department Chair"),
            )
        else:
            return cls(
                name=data["name"],
                age=data["age"],
                email=data["email"],
                student_id=data["student_id"],
                department=data["department"],
                course=data["course"],
                semester=data["semester"],
                cgpa=data["cgpa"],
                student_type="general",
            )

    def __eq__(self, other: object) -> bool:
        """Students are uniquely distinguished by student_id."""
        if not isinstance(other, Student):
            return False
        return self.student_id == other.student_id

    def __hash__(self) -> int:
        return hash(self.student_id)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.student_id!r}, name={self.name!r}, "
            f"dept={self.department!r}, sem={self.semester}, cgpa={self.cgpa})"
        )


@dataclass
class UndergraduateStudent(Student):
    """Specialized student class for undergraduate degree candidates.

    Undergraduate programs span 1 to 8 semesters and track academic advisors
    and internship status.

    Attributes:
        academic_advisor: Name of assigned faculty advisor.
        internship_status: Internship fulfillment status.
    """

    academic_advisor: str = "General Advisor"
    internship_status: str = "Not Started"
    student_type: str = "undergraduate"

    # Standard undergraduate semester limits: 1 through 8
    MIN_SEMESTER: int = 1
    MAX_SEMESTER: int = 8

    def __post_init__(self) -> None:
        """Validate undergraduate specifics."""
        self.academic_advisor = str(self.academic_advisor).strip() or "General Advisor"
        self.internship_status = str(self.internship_status).strip() or "Not Started"
        super().__post_init__()

    @property
    def academic_standing(self) -> str:
        """Calculate undergraduate honors standing based on CGPA.

        Returns:
            'Dean\'s List', 'Good Standing', or 'Academic Warning'.
        """
        if self.cgpa >= 8.5:
            return "Dean's List"
        elif self.cgpa >= 5.0:
            return "Good Standing"
        return "Academic Warning"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize undergraduate student."""
        data = super().to_dict()
        data.update(
            {
                "academic_advisor": self.academic_advisor,
                "internship_status": self.internship_status,
                "academic_standing": self.academic_standing,
            }
        )
        return data


@dataclass
class PostgraduateStudent(Student):
    """Specialized student class for postgraduate / master / doctoral candidates.

    Postgraduate programs span 1 to 6 semesters and track research topics
    and thesis supervisors.

    Attributes:
        research_topic: Title or subject of graduate research.
        thesis_supervisor: Assigned research supervisor.
    """

    research_topic: str = "General Research"
    thesis_supervisor: str = "Department Chair"
    student_type: str = "postgraduate"

    # Standard postgraduate semester limits: 1 through 6
    MIN_SEMESTER: int = 1
    MAX_SEMESTER: int = 6

    def __post_init__(self) -> None:
        """Validate postgraduate specifics."""
        self.research_topic = str(self.research_topic).strip() or "General Research"
        self.thesis_supervisor = str(self.thesis_supervisor).strip() or "Department Chair"
        super().__post_init__()

    @property
    def defense_eligible(self) -> bool:
        """Determine if postgraduate student is eligible for thesis defense.

        Eligible if student has completed at least 3 semesters, has CGPA >= 7.0,
        and has an assigned research topic.
        """
        return (
            self.semester >= 3
            and self.cgpa >= 7.0
            and bool(self.research_topic)
            and self.research_topic != "TBD"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize postgraduate student."""
        data = super().to_dict()
        data.update(
            {
                "research_topic": self.research_topic,
                "thesis_supervisor": self.thesis_supervisor,
                "defense_eligible": self.defense_eligible,
            }
        )
        return data
