import re


NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10
}


def convert_number(value):
    value = value.lower().strip()

    if value.isdigit():
        return int(value)

    return NUMBER_WORDS.get(value)


def build_knowledge_base(document_text):

    text = document_text.lower()
    kb = {}

    # 1. Student borrowing information
    student = re.search(
        r"students can borrow a maximum of "
        r"(\w+|\d+) books.*?for (\d+) days",
        text
    )

    if student:
        max_books = convert_number(student.group(1))

        if max_books is not None:
            kb["student"] = {
                "max_books": max_books,
                "loan_days": int(student.group(2))
            }

    # 2. Faculty borrowing information
    faculty = re.search(
        r"faculty members can borrow a maximum of "
        r"(\w+|\d+) books.*?for (\d+) days",
        text
    )

    if faculty:
        max_books = convert_number(faculty.group(1))

        if max_books is not None:
            kb["faculty"] = {
                "max_books": max_books,
                "loan_days": int(faculty.group(2))
            }

    # 3. Late fine information
    fine = re.search(
        r"(?:late\s+)?fine(?:\s+of|\s+is|:)?\s*"
        r"[₹]?\s*(\d+)\s*"
        r"(?:rupees|rs)?\s*per book per day",
        text
    )

    if fine:
        kb["fine_per_book_per_day"] = int(fine.group(1))

    # 4. Weekday timings
    weekday = re.search(
        r"operates from\s*(.*?)\s+to\s+(.*?)\s+on weekdays",
        text
    )

    if weekday:
        kb["weekday_timings"] = {
            "opening": weekday.group(1).strip(),
            "closing": weekday.group(2).strip()
        }

    # 5. Weekend timings
    weekend = re.search(
        r"saturdays and sundays.*?operates from\s*"
        r"(.*?)\s+to\s+(.*?)(?:\.|\n|$)",
        text
    )

    if weekend:
        kb["weekend_timings"] = {
            "opening": weekend.group(1).strip(),
            "closing": weekend.group(2).strip()
        }

    # 6. Membership information
    if (
        "registered university students and faculty" in text
        and re.search(
            r"visitors?.{0,50}do not have borrowing privileges",
            text
        )
    ):
        kb["membership"] = {
            "students": True,
            "faculty": True,
            "visitors": False
        }

    # 7. Reference book restrictions
    if "reference books" in text:

        reference_books = {}

        if "cannot be borrowed" in text:
            reference_books["borrowing_allowed"] = False

        if "reading inside the library" in text:
            reference_books["usage"] = "Reading inside the library"

        if reference_books:
            kb["reference_books"] = reference_books

    # 8. Renewal information
    if "renewed once" in text:
        kb["renewal"] = {
            "maximum_renewals": 1,
            "condition": "No other member has reserved the book"
        }

    # 9. Library facilities
    facilities = []

    facility_options = {
        "reading rooms": ["reading rooms", "reading room"],
        "computer access": ["computer access"],
        "Wi-Fi": ["wi-fi", "wifi"],
        "digital resources": ["digital resources"]
    }

    for facility, phrases in facility_options.items():

        if any(phrase in text for phrase in phrases):
            facilities.append(facility)

    if facilities:
        kb["facilities"] = facilities

    # 10. Computer session duration
    computer = re.search(
        r"computer sessions? (?:is|are)?\s*"
        r"limited to (\d+) minutes",
        text
    )

    if computer:
        kb["computer_session_minutes"] = int(
            computer.group(1)
        )

    # Computer session restriction condition
    if "when other users are waiting" in text:
        kb["computer_session_condition"] = (
            "When other users are waiting"
        )

    # 11. Public holiday information
    if re.search(
        r"closed on public holidays",
        text
    ):
        kb["public_holidays"] = {
            "closed": True
        }

    return kb


def display_knowledge_base(kb):

    print("\nKNOWLEDGE BASE")
    print("=" * 45)

    for category, information in kb.items():

        print(f"\n{category.upper()}")

        if isinstance(information, dict):

            for attribute, value in information.items():
                print(f"  {attribute}: {value}")

        else:
            print(f"  {information}")