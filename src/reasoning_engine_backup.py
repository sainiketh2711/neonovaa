import re


# Different words that can indicate the same topic
TOPIC_KEYWORDS = {
    "timings": [
        "timing", "times", "hours", "open", "opening",
        "close", "closing", "weekdays", "weekends",
        "saturday", "sunday"
    ],

    "student": [
        "student", "students"
    ],

    "faculty": [
        "faculty", "professor", "teachers", "staff"
    ],

    "fine": [
        "fine", "penalty", "charge", "overdue",
        "late", "return"
    ],

    "membership": [
        "membership", "member", "eligible", "eligibility",
        "visitor", "registered"
    ],

    "reference": [
        "reference", "reference book"
    ],

    "renewal": [
        "renew", "renewal", "extend", "extension",
        "reserved", "reservation"
    ],

    "facilities": [
        "facility", "facilities", "services", "wifi",
        "wi-fi", "reading room", "digital resources"
    ],

    "computer": [
        "computer", "computers", "session", "usage"
    ],

    "holiday": [
        "holiday", "holidays", "public holiday"
    ]
}


def identify_topics(question):
    question = question.lower()

    identified_topics = []

    for topic, keywords in TOPIC_KEYWORDS.items():

        for keyword in keywords:

            if keyword in question:
                identified_topics.append(topic)
                break

    return identified_topics


def answer_topic(topic, question, knowledge_base):

    question = question.lower()

    # Library timings
    if topic == "timings":

        if "weekend" in question or "saturday" in question or "sunday" in question:

            timings = knowledge_base.get("weekend_timings")

            if timings:
                return (
                    f"Weekend timings are from "
                    f"{timings['opening']} to {timings['closing']}."
                )

        timings = knowledge_base.get("weekday_timings")

        if timings:
            return (
                f"Weekday timings are from "
                f"{timings['opening']} to {timings['closing']}."
            )

    # Student information
    if topic == "student":

        student = knowledge_base.get("student")

        if student:

            # Check if the question asks for a borrowing comparison
            numbers = re.findall(r"\d+", question)

            if numbers and any(
                word in question
                for word in ["can", "allowed", "maximum", "limit"]
            ):

                requested_books = int(numbers[0])

                if requested_books <= student["max_books"]:
                    return (
                        f"Students are allowed to borrow up to "
                        f"{student['max_books']} books. "
                        f"Borrowing {requested_books} books is within the limit."
                    )

                return (
                    f"Students can borrow a maximum of "
                    f"{student['max_books']} books. "
                    f"Borrowing {requested_books} books exceeds the limit."
                )

            return (
                f"Students can borrow a maximum of "
                f"{student['max_books']} books for "
                f"{student['loan_days']} days."
            )

    # Faculty information
    if topic == "faculty":

        faculty = knowledge_base.get("faculty")

        if faculty:
            return (
                f"Faculty members can borrow a maximum of "
                f"{faculty['max_books']} books for "
                f"{faculty['loan_days']} days."
            )

    # Fine calculation
    if topic == "fine":

        fine_rate = knowledge_base.get(
            "fine_per_book_per_day"
        )

        if fine_rate is not None:

            numbers = re.findall(r"\d+", question)

            if numbers:

                overdue_days = int(numbers[0])

                # Check if number of books is also mentioned
                if len(numbers) >= 2:

                    number_of_books = int(numbers[1])

                    total_fine = (
                        overdue_days
                        * number_of_books
                        * fine_rate
                    )

                    return (
                        f"The fine for {number_of_books} books "
                        f"overdue by {overdue_days} days is "
                        f"₹{total_fine}."
                    )

                total_fine = overdue_days * fine_rate

                return (
                    f"The fine for {overdue_days} overdue days "
                    f"is ₹{total_fine} per book."
                )

            return (
                f"The late fine is ₹{fine_rate} "
                f"per book per day."
            )

    # Membership
    if topic == "membership":

        membership = knowledge_base.get("membership")

        if membership:

            if "visitor" in question:
                return (
                    "Visitors are not eligible for borrowing privileges."
                )

            return (
                "Registered university students and faculty members "
                "are eligible for library membership."
            )

    # Reference books
    if topic == "reference":

        reference_books = knowledge_base.get(
            "reference_books"
        )

        if reference_books:
            return (
                "Reference books cannot be borrowed. "
                "They are available for reading inside the library."
            )

    # Renewal
    if topic == "renewal":

        renewal = knowledge_base.get("renewal")

        if renewal:
            return (
                f"Books may be renewed "
                f"{renewal['maximum_renewals']} time, provided "
                f"{renewal['condition'].lower()}."
            )

    # Facilities
    if topic == "facilities":

        return (
            "The library provides reading rooms, computer access, "
            "Wi-Fi, and digital resources to registered members."
        )

    # Computer usage
    if topic == "computer":

        duration = knowledge_base.get(
            "computer_session_minutes"
        )

        if duration:
            return (
                f"Computer sessions are limited to "
                f"{duration} minutes when other users are waiting."
            )

    # Holidays
    if topic == "holiday":

        return (
            "The library remains closed on public holidays."
        )

    return None


def process_with_reasoning(question, knowledge_base):

    topics = identify_topics(question)

    if not topics:
        return (
            "The system could not identify a relevant topic "
            "in the Knowledge Base."
        )

    answers = []

    for topic in topics:

        answer = answer_topic(
            topic,
            question,
            knowledge_base
        )

        if answer and answer not in answers:
            answers.append(answer)

    if answers:
        return "\n".join(answers)

    return (
        "Sorry, the requested information is not available "
        "in the Knowledge Base."
    )