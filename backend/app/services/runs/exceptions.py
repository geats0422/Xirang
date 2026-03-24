from __future__ import annotations


class RunNotFoundError(Exception):
    pass


class DuplicateAnswerError(Exception):
    pass


class InvalidRunStateError(Exception):
    pass


class RunNotCompletedError(Exception):
    pass


class QuestionNotFoundError(Exception):
    pass
