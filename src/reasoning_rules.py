import re


TOPIC_KEYWORDS = {

    "timings": [
        "timing", "timings", "hours", "opening",
        "closing", "open", "close", "schedule",
        "weekday", "weekdays", "weekend",
        "weekends", "saturday", "sunday"
    ],

    "student": [
        "student", "students", "undergraduate",
        "undergraduates", "learner", "learners",
        "scholar"
    ],

    "faculty": [
        "faculty", "professor", "professors",
        "teacher", "teachers", "lecturer",
        "lecturers", "staff"
    ],

    "fine": [
        "fine", "penalty", "charge", "overdue",
        "late", "payment", "pay", "cost", "owing"
    ],

    "membership": [
        "membership", "member", "eligible",
        "eligibility", "visitor", "visitors",
        "registered", "registration"
    ],

    "reference": [
        "reference", "reference book",
        "reference books", "inside reading"
    ],

    "renewal": [
        "renew", "renewal", "renewed",
        "extend", "extension", "reserved",
        "reservation"
    ],

    "facilities": [
        "facility", "facilities", "services",
        "amenities", "wifi", "wi-fi",
        "reading room", "digital resources"
    ],

    "computer": [
        "computer", "computers", "session",
        "sessions", "computer access"
    ],

    "holiday": [
        "holiday", "holidays",
        "public holiday", "public holidays"
    ]
}


def normalize_question(question):

    question = question.lower()

    question = re.sub(
        r"[^a-z0-9₹\s]",
        " ",
        question
    )

    question = re.sub(r"\s+", " ", question)

    return question.strip()


def identify_topics(question):

    normalized = normalize_question(question)

    identified_topics = []

    for topic, keywords in TOPIC_KEYWORDS.items():

        for keyword in keywords:

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(keyword)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, normalized):

                identified_topics.append(topic)
                break

    return identified_topics


def split_questions(question):

    parts = re.split(
        r"[?!;\n]+",
        question
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def extract_quantity(question, unit):

    pattern = (
        r"(\d+)\s*"
        + re.escape(unit)
        + r"\b"
    )

    match = re.search(
        pattern,
        question.lower()
    )

    if match:
        return int(match.group(1))

    return None