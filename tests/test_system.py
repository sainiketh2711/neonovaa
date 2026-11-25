import sys
import unittest

from pathlib import Path

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
SOURCE_FOLDER = PROJECT_FOLDER / "src"

sys.path.insert(0, str(SOURCE_FOLDER))

from knowledge_base import build_knowledge_base
from reasoning_engine import process_with_reasoning


SAMPLE_DOCUMENT = """
The library operates from 8:00 AM to 8:00 PM on weekdays.
On Saturdays and Sundays, the library operates from 9:00 AM to 5:00 PM.

Students can borrow a maximum of three books for 14 days.
Faculty members can borrow a maximum of five books for 30 days.

The late fine is ₹2 per book per day.

Registered university students and faculty members are eligible for membership.
Visitors do not have borrowing privileges.

Reference books are for inside reading only and cannot be borrowed.

Books may be renewed once if no other member has reserved them.

The library provides reading rooms, computer access, Wi-Fi, and digital resources.

Computer sessions are limited to 30 minutes when others are waiting.

The library is closed on public holidays.
"""


class TestLibraryQuestionAnswering(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kb = build_knowledge_base(SAMPLE_DOCUMENT)

    def ask(self, question):
        return process_with_reasoning(question, self.kb).lower()

    def test_student_borrowing(self):
        answer = self.ask("How many books can students borrow?")
        self.assertIn("3 books", answer)
        self.assertIn("14 days", answer)

    def test_faculty_borrowing(self):
        answer = self.ask("What is the faculty borrowing limit?")
        self.assertIn("5 books", answer)
        self.assertIn("30 days", answer)

    def test_fine_calculation(self):
        answer = self.ask(
            "What is the fine for 3 books overdue by 5 days?"
        )
        self.assertIn("₹30", answer)

    def test_reference_books(self):
        answer = self.ask(
            "Can I take reference books outside?"
        )
        self.assertIn("cannot be borrowed", answer)

    def test_renewal(self):
        answer = self.ask(
            "Can I renew a book if another member reserved it?"
        )
        self.assertIn("reserved", answer)

    def test_visitor_membership(self):
        answer = self.ask(
            "Can visitors borrow books?"
        )
        self.assertIn("visitors", answer)
        self.assertIn("not have borrowing privileges", answer)

    def test_weekday_timings(self):
        answer = self.ask(
            "What are the library timings on weekdays?"
        )
        self.assertIn("8:00 am", answer)
        self.assertIn("8:00 pm", answer)

    def test_weekend_timings(self):
        answer = self.ask(
            "What are the library timings on Sundays?"
        )
        self.assertIn("9:00 am", answer)
        self.assertIn("5:00 pm", answer)

    def test_computer_limit(self):
        answer = self.ask(
            "How long can I use a computer?"
        )
        self.assertIn("30 minutes", answer)

    def test_holiday(self):
        answer = self.ask(
            "Is the library open on public holidays?"
        )
        self.assertIn("closed", answer)

    def test_multiple_questions(self):
        answer = self.ask(
            "What are the library timings? "
            "How many books can students borrow? "
            "What is the late fine?"
        )

        self.assertIn("8:00 am", answer)
        self.assertIn("3 books", answer)
        self.assertIn("per book per day", answer)

    def test_student_faculty_comparison(self):
        answer = self.ask(
            "Compare student and faculty borrowing limits."
        )

        self.assertIn("3 books", answer)
        self.assertIn("5 books", answer)

    def test_unknown_question(self):
        answer = self.ask(
            "Does the library provide a printing service?"
        )

        self.assertIn("could not be identified", answer)


if __name__ == "__main__":
    unittest.main(verbosity=2)