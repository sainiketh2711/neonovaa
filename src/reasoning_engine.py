import re

from reasoning_rules import (
    identify_topics,
    split_questions,
    extract_quantity
)


def answer_timings(question, kb):

    if any(word in question.lower() for word in [
        "weekend", "weekends", "saturday", "sunday"
    ]):

        timings = kb.get("weekend_timings")

        if timings:
            return (
                f"Weekend timings are from "
                f"{timings['opening']} to {timings['closing']}."
            )

    timings = kb.get("weekday_timings")

    if timings:
        return (
            f"Weekday timings are from "
            f"{timings['opening']} to {timings['closing']}."
        )

    return None


def answer_student(question, kb):

    student = kb.get("student")

    if not student:
        return None

    requested_books = extract_quantity(question, "books")

    if requested_books is not None and any(
        word in question.lower()
        for word in ["can", "allowed", "borrow", "limit"]
    ):

        maximum = student["max_books"]

        if requested_books <= maximum:
            return (
                f"Students can borrow up to {maximum} books. "
                f"Borrowing {requested_books} books is within the limit."
            )

        return (
            f"Students can borrow a maximum of {maximum} books. "
            f"Borrowing {requested_books} books exceeds the limit."
        )

    return (
        f"Students can borrow a maximum of "
        f"{student['max_books']} books for "
        f"{student['loan_days']} days."
    )


def answer_faculty(question, kb):

    faculty = kb.get("faculty")

    if not faculty:
        return None

    requested_books = extract_quantity(question, "books")

    if requested_books is not None and any(
        word in question.lower()
        for word in ["can", "allowed", "borrow", "limit"]
    ):

        maximum = faculty["max_books"]

        if requested_books <= maximum:
            return (
                f"Faculty members can borrow up to {maximum} books. "
                f"Borrowing {requested_books} books is within the limit."
            )

        return (
            f"Faculty members can borrow a maximum of {maximum} books. "
            f"Borrowing {requested_books} books exceeds the limit."
        )

    return (
        f"Faculty members can borrow a maximum of "
        f"{faculty['max_books']} books for "
        f"{faculty['loan_days']} days."
    )


def answer_fine(question, kb):

    rate = kb.get("fine_per_book_per_day")

    if rate is None:
        return None

    days = extract_quantity(question, "days")
    books = extract_quantity(question, "books")

    if days is not None and books is not None:

        total = days * books * rate

        return (
            f"The fine for {books} books overdue by "
            f"{days} days is ₹{total}. "
            f"Calculation: {books} × {days} × ₹{rate} = ₹{total}."
        )

    if days is not None:

        total = days * rate

        return (
            f"The fine for {days} overdue days is "
            f"₹{total} per book."
        )

    return f"The late fine is ₹{rate} per book per day."


def answer_membership(question, kb):

    membership = kb.get("membership")

    if not membership:
        return None

    if "visitor" in question.lower():
        return (
            "Visitors do not have borrowing privileges."
        )

    return (
        "Registered university students and faculty members "
        "are eligible for library membership."
    )


def answer_reference(kb):

    reference = kb.get("reference_books")

    if reference and not reference["borrowing_allowed"]:
        return (
            "Reference books cannot be borrowed. "
            "They are available for reading inside the library."
        )

    return None


def answer_renewal(question, kb):

    renewal = kb.get("renewal")

    if not renewal:
        return None

    condition = renewal["condition"]

    if "reserved" in question.lower():
        return (
            f"Books may be renewed "
            f"{renewal['maximum_renewals']} time, provided "
            f"{condition.lower()}."
        )

    return (
        f"Books may be renewed "
        f"{renewal['maximum_renewals']} time, provided "
        f"{condition.lower()}."
    )


def answer_facilities(kb):

    facilities = kb.get("facilities")

    if not facilities:
        return None

    return (
        "The library provides "
        + ", ".join(facilities[:-1])
        + (" and " if len(facilities) > 1 else "")
        + (facilities[-1] if facilities else "")
        + "."
    )


def answer_computer(kb):

    duration = kb.get("computer_session_minutes")

    if duration is None:
        return None

    return (
        f"Computer sessions are limited to {duration} minutes "
        "when other users are waiting."
    )


def answer_holiday(kb):

    holiday = kb.get("public_holidays")

    if holiday and holiday["closed"]:
        return "The library remains closed on public holidays."

    return None


def answer_comparison(topics, kb):

    if "student" not in topics or "faculty" not in topics:
        return None

    student = kb.get("student")
    faculty = kb.get("faculty")

    if not student or not faculty:
        return None

    return (
        "Borrowing comparison: "
        f"Students can borrow {student['max_books']} books "
        f"for {student['loan_days']} days, while faculty members "
        f"can borrow {faculty['max_books']} books "
        f"for {faculty['loan_days']} days."
    )


def answer_topic(topic, question, kb):

    if topic == "timings":
        return answer_timings(question, kb)

    if topic == "student":
        return answer_student(question, kb)

    if topic == "faculty":
        return answer_faculty(question, kb)

    if topic == "fine":
        return answer_fine(question, kb)

    if topic == "membership":
        return answer_membership(question, kb)

    if topic == "reference":
        return answer_reference(kb)

    if topic == "renewal":
        return answer_renewal(question, kb)

    if topic == "facilities":
        return answer_facilities(kb)

    if topic == "computer":
        return answer_computer(kb)

    if topic == "holiday":
        return answer_holiday(kb)

    return None


def process_with_reasoning(question, knowledge_base):

    question_parts = split_questions(question)

    all_answers = []

    for part in question_parts:

        topics = identify_topics(part)

        if not topics:
            continue

        # Handle direct student/faculty comparison
        comparison_words = [
            "compare", "comparison", "difference",
            "differ", "versus", "vs"
        ]

        if (
            any(word in part.lower() for word in comparison_words)
            and "student" in topics
            and "faculty" in topics
        ):

            comparison = answer_comparison(
                topics,
                knowledge_base
            )

            if comparison and comparison not in all_answers:
                all_answers.append(comparison)

            continue

        for topic in topics:

            answer = answer_topic(
                topic,
                part,
                knowledge_base
            )

            if answer and answer not in all_answers:
                all_answers.append(answer)

    if all_answers:
        return "\n\n".join(all_answers)

    return (
        "The requested information could not be identified "
        "in the Knowledge Base."
    )