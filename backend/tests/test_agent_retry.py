from app.services.agent_service import _is_transient_gemini_error


class DummyError(Exception):
    def __init__(self, code):
        super().__init__(str(code))
        self.status_code = code


def test_transient_gemini_errors_are_retried():
    for code in (429, 500, 502, 503, 504):
        assert _is_transient_gemini_error(DummyError(code)) is True


def test_auth_error_is_not_retried():
    assert _is_transient_gemini_error(DummyError(401)) is False
