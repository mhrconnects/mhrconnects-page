"""Regression tests over the messy-message corpus (tests/corpus.py).

Honest note: the corpus was used to tune the rules, so a high score here
means "no regressions", NOT "95% accurate in the real world". On fresh,
unseen messages the keyword rules scored about 77%. Real accuracy is
measured by adding NEW messages to corpus.py BEFORE fixing the rules.
"""
import unittest

from src.classifier import classify
from src.responder import respond
from tests.corpus import CORPUS

SAFETY = {"allergy", "complaint", "human"}


class TestCorpus(unittest.TestCase):
    def test_overall_accuracy_has_not_regressed(self):
        wrong = [(m, e, classify(m).category) for m, e in CORPUS
                 if classify(m).category != e]
        self.assertLessEqual(len(wrong), len(CORPUS) * 0.05, wrong)

    def test_safety_messages_never_get_an_automatic_answer(self):
        """The one mistake we must never make: treating an allergy, complaint
        or request for a person as an order, booking, FAQ or small talk."""
        for m, expected in CORPUS:
            if expected in SAFETY:
                r = classify(m)
                self.assertTrue(r.needs_human,
                                f"UNSAFE: {m!r} -> {r.category}, no human")

    def test_safety_messages_get_a_handoff_reply(self):
        for m, expected in CORPUS:
            if expected in SAFETY:
                r = respond(m)
                self.assertTrue(r.needs_human, m)
                self.assertNotIn("TODO", r.reply, m)

    def test_no_reply_leaks_todo_for_any_corpus_message(self):
        for m, _ in CORPUS:
            self.assertNotIn("TODO", respond(m).reply, m)

    def test_greetings_get_friendly_reply_not_a_callback(self):
        for m in ["hi", "thanks", "bye", "cheers"]:
            r = respond(m)
            self.assertFalse(r.needs_human, m)
            self.assertEqual(r.category, "chitchat")

    def test_open_late_is_a_question_not_a_complaint(self):
        self.assertEqual(classify("are you open late").category, "faq")


if __name__ == "__main__":
    unittest.main()
