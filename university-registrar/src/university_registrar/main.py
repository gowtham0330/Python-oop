"""Command-Line Interface (CLI) for the University Registrar System.

Provides commands to add, list, search, view, update, delete, export, import,
and inspect statistics for student records using argparse.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from university_registrar.exceptions import (
    DuplicateStudentError,
    RegistrarError,
    StudentNotFoundError,
    StorageError,
    UnsupportedFormatError,
    ValidationError,
)
from university_registrar.models import (
    PostgraduateStudent,
    Student,
    UndergraduateStudent,
)
from university_registrar.registrar import UniversityRegistrar

DEFAULT_STORAGE_FILE = Path("data/students.json")


def format_student_row(s: Student) -> str:
    """Format student details into a formatted summary line."""
    type_tag = (
        "UG" if isinstance(s, UndergraduateStudent)
        else "PG" if isinstance(s, PostgraduateStudent)
        else "GEN"
    )
    extra = ""
    if isinstance(s, UndergraduateStudent):
        extra = f" | Advisor: {s.academic_advisor} [{s.academic_standing}]"
    elif isinstance(s, PostgraduateStudent):
        defense = "Defense Ready" if s.defense_eligible else "Thesis In-Progress"
        extra = f" | Supv: {s.thesis_supervisor} [{defense}]"

    return (
        f"[{type_tag}] {s.student_id:<12} {s.name:<22} "
        f"{s.department:<20} Sem:{s.semester:<2} CGPA:{s.cgpa:.2f}{extra}"
    )


def handle_add(registrar: UniversityRegistrar, args: argparse.Namespace) -> int:
    """Handle adding a new student, interactively or via CLI flags."""
    try:
        # Check if arguments provided via flags
        if args.id and args.name and args.email:
            sid = args.id
            name = args.name
            email = args.email
            age = args.age or 20
            dept = args.dept or "Computer Science"
            course = args.course or "B.Tech Computer Science"
            semester = args.semester or 1
            cgpa = args.cgpa if args.cgpa is not None else 8.0
            stype = (args.type or "undergraduate").lower()
            advisor = args.advisor or "Dr. Smith"
            supervisor = args.supervisor or "Dr. Johnson"
            research = args.research or "Distributed Systems"
        else:
            # Interactive prompt
            print("\n--- Register New Student (Interactive) ---")
            stype = input("Student Type (undergraduate/postgraduate) [undergraduate]: ").strip().lower() or "undergraduate"
            sid = input("Student ID (e.g., UG-2024-001): ").strip()
            name = input("Full Name: ").strip()
            email = input("Email: ").strip()
            age_raw = input("Age [20]: ").strip() or "20"
            dept = input("Department [Computer Science]: ").strip() or "Computer Science"
            course = input("Course [B.Tech CS]: ").strip() or "B.Tech CS"
            sem_raw = input("Semester [1]: ").strip() or "1"
            cgpa_raw = input("CGPA (0.0 - 10.0) [8.5]: ").strip() or "8.5"

            age = int(age_raw)
            semester = int(sem_raw)
            cgpa = float(cgpa_raw)

            advisor = "General Advisor"
            supervisor = "Department Chair"
            research = "General Research"

            if stype in {"undergraduate", "ug"}:
                advisor = input("Academic Advisor [Dr. Alice]: ").strip() or "Dr. Alice"
            else:
                supervisor = input("Thesis Supervisor [Dr. Bob]: ").strip() or "Dr. Bob"
                research = input("Research Topic [Machine Learning]: ").strip() or "Machine Learning"

        # Instantiate subtype
        if stype in {"undergraduate", "ug", "undergrad"}:
            student = UndergraduateStudent(
                student_id=sid,
                name=name,
                email=email,
                age=age,
                department=dept,
                course=course,
                semester=semester,
                cgpa=cgpa,
                academic_advisor=advisor,
            )
        elif stype in {"postgraduate", "pg", "postgrad"}:
            student = PostgraduateStudent(
                student_id=sid,
                name=name,
                email=email,
                age=age,
                department=dept,
                course=course,
                semester=semester,
                cgpa=cgpa,
                thesis_supervisor=supervisor,
                research_topic=research,
            )
        else:
            student = Student(
                student_id=sid,
                name=name,
                email=email,
                age=age,
                department=dept,
                course=course,
                semester=semester,
                cgpa=cgpa,
            )

        registrar.add_student(student)
        print(f"✓ Successfully registered student: {student.student_id} ({student.name})")
        return 0

    except ValidationError as err:
        print(f"✗ Validation Error: {err}", file=sys.stderr)
        return 1
    except DuplicateStudentError as err:
        print(f"✗ Duplicate Error: {err}", file=sys.stderr)
        return 2
    except RegistrarError as err:
        print(f"✗ Error: {err}", file=sys.stderr)
        return 3


def handle_list(registrar: UniversityRegistrar, args: argparse.Namespace) -> int:
    """List enrolled students with filtering and sorting."""
    students = registrar.list_students(sort_by=args.sort)
    if args.dept:
        students = [s for s in students if s.department.lower() == args.dept.lower()]
    if args.type:
        students = registrar.filter_by_type(args.type)

    if not students:
        print("No student records found matching the criteria.")
        return 0

    print(f"\nFound {len(students)} student record(s):")
    print("-" * 90)
    for s in students:
        print(format_student_row(s))
    print("-" * 90)
    return 0


def handle_get(registrar: UniversityRegistrar, args: argparse.Namespace) -> int:
    """Retrieve full details of a single student."""
    try:
        s = registrar.get_student(args.id)
        print("\n--- Student Details ---")
        for k, v in s.to_dict().items():
            formatted_key = k.replace("_", " ").title()
            print(f"  {formatted_key:<20}: {v}")
        return 0
    except StudentNotFoundError as err:
        print(f"✗ Not Found: {err}", file=sys.stderr)
        return 2


def handle_search(registrar: UniversityRegistrar, args: argparse.Namespace) -> int:
    """Search students by keyword."""
    results = registrar.search_students(args.query)
    if not results:
        print(f"No students found matching query: '{args.query}'")
        return 0

    print(f"\nSearch results for '{args.query}' ({len(results)} matches):")
    print("-" * 90)
    for s in results:
        print(format_student_row(s))
    print("-" * 90)
    return 0


def handle_delete(registrar: UniversityRegistrar, args: argparse.Namespace) -> int:
    """Delete a student by ID."""
    try:
        deleted = registrar.delete_student(args.id)
        print(f"✓ Successfully deleted student: {deleted.student_id} ({deleted.name})")
        return 0
    except StudentNotFoundError as err:
        print(f"✗ Not Found: {err}", file=sys.stderr)
        return 2


def handle_export(registrar: UniversityRegistrar, args: argparse.Namespace) -> int:
    """Export records to a destination JSON or CSV file."""
    try:
        count = registrar.export_students(args.file)
        print(f"✓ Successfully exported {count} record(s) to '{args.file}'")
        return 0
    except UnsupportedFormatError as err:
        print(f"✗ Format Error: {err}", file=sys.stderr)
        return 1
    except StorageError as err:
        print(f"✗ Storage Error: {err}", file=sys.stderr)
        return 3


def handle_import(registrar: UniversityRegistrar, args: argparse.Namespace) -> int:
    """Import records from an external JSON or CSV file."""
    try:
        count = registrar.import_students(args.file, merge=args.merge)
        print(f"✓ Successfully imported {count} student record(s) from '{args.file}'")
        return 0
    except (ValidationError, DuplicateStudentError) as err:
        print(f"✗ Import Rejected (Transaction Aborted): {err}", file=sys.stderr)
        return 1
    except UnsupportedFormatError as err:
        print(f"✗ Unsupported File Format: {err}", file=sys.stderr)
        return 2
    except StorageError as err:
        print(f"✗ Storage Error: {err}", file=sys.stderr)
        return 3


def handle_stats(registrar: UniversityRegistrar, _args: argparse.Namespace) -> int:
    """Print comprehensive registrar analytics."""
    stats = registrar.get_statistics()
    print("\n========================================")
    print("      UNIVERSITY REGISTRAR METRICS      ")
    print("========================================")
    print(f" Total Registered Students : {stats['total_students']}")
    print(f" Undergraduates            : {stats['undergraduate_count']}")
    print(f" Postgraduates             : {stats['postgraduate_count']}")
    print(f" Average CGPA              : {stats['average_cgpa']:.2f}")
    print(f" Highest CGPA              : {stats['highest_cgpa']:.2f}")
    print(f" Lowest CGPA               : {stats['lowest_cgpa']:.2f}")
    print(f" Dean's List (Honors)      : {stats['dean_list_count']}")
    print(f" Thesis Defense Eligible   : {stats['defense_eligible_count']}")
    print("\n--- Department Breakdown ---")
    for dept, cnt in stats["department_counts"].items():
        print(f"  {dept:<25}: {cnt}")
    print("\n--- CGPA Distribution ---")
    for bracket, cnt in stats["cgpa_distribution"].items():
        print(f"  {bracket:<25}: {cnt}")
    print("========================================\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="university-registrar",
        description="University Registrar: Object-Oriented Data Management System.",
    )
    parser.add_argument(
        "-d",
        "--data-file",
        default=str(DEFAULT_STORAGE_FILE),
        help="Path to persistent storage file (.json or .csv). Default: data/students.json",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available registrar operations")

    # add
    p_add = subparsers.add_parser("add", help="Register a new student")
    p_add.add_argument("--id", help="Student unique identifier (e.g. UG-2024-001)")
    p_add.add_argument("--name", help="Student full legal name")
    p_add.add_argument("--email", help="Student contact email")
    p_add.add_argument("--age", type=int, help="Student age (years)")
    p_add.add_argument("--dept", help="Department name")
    p_add.add_argument("--course", help="Degree / course name")
    p_add.add_argument("--semester", type=int, help="Current semester")
    p_add.add_argument("--cgpa", type=float, help="Cumulative GPA (0.0 to 10.0)")
    p_add.add_argument("--type", choices=["undergraduate", "postgraduate"], help="Student level")
    p_add.add_argument("--advisor", help="Undergraduate academic advisor")
    p_add.add_argument("--supervisor", help="Postgraduate thesis supervisor")
    p_add.add_argument("--research", help="Postgraduate research topic")

    # list
    p_list = subparsers.add_parser("list", help="List all registered students")
    p_list.add_argument("--dept", help="Filter by department")
    p_list.add_argument("--type", choices=["undergraduate", "postgraduate"], help="Filter by type")
    p_list.add_argument("--sort", choices=["id", "name", "department", "cgpa"], default="id", help="Sort order")

    # get
    p_get = subparsers.add_parser("get", help="Get details for a specific student ID")
    p_get.add_argument("id", help="Target student ID")

    # search
    p_search = subparsers.add_parser("search", help="Search students across attributes")
    p_search.add_argument("query", help="Search term")

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete student by ID")
    p_delete.add_argument("id", help="Target student ID to delete")

    # export
    p_export = subparsers.add_parser("export", help="Export students to JSON or CSV")
    p_export.add_argument("file", help="Export target file path (.json or .csv)")

    # import
    p_import = subparsers.add_parser("import", help="Import students from JSON or CSV")
    p_import.add_argument("file", help="Source file path (.json or .csv)")
    p_import.add_argument("--merge", action="store_true", default=True, help="Merge into existing records")

    # stats
    subparsers.add_parser("stats", help="Display summary metrics and distributions")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI application entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # Initialize registrar with storage file
    data_path = Path(args.data_file)
    registrar = UniversityRegistrar(storage_path=data_path, auto_save=True)

    handlers = {
        "add": handle_add,
        "list": handle_list,
        "get": handle_get,
        "search": handle_search,
        "delete": handle_delete,
        "export": handle_export,
        "import": handle_import,
        "stats": handle_stats,
    }

    handler = handlers.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(registrar, args)


if __name__ == "__main__":
    sys.exit(main())
