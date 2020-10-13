from hasjob.utils import redactemail


class TestUtils:
    def test_redactemail(self):
        message = "Send email to test@example.com and you are all set."
        expected_message = "Send email to [redacted] and you are all set."
        assert redactemail(message) == expected_message
