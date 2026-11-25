from reasoning_rules import (
    identify_topics,
    split_questions,
    normalize_question
)


def process_question_structure(question):

    question_parts = split_questions(question)

    processed_questions = []

    for part in question_parts:

        topics = identify_topics(part)

        processed_questions.append({
            "original_question": part,
            "normalized_question": normalize_question(part),
            "topics": topics
        })

    return processed_questions