import re

# Patterns for personal details that students sometimes type into comments
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
LINK = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
HANDLE = re.compile(r"(?<!\w)@\w{2,}")
PHONE = re.compile(r"(?<![\w])\+?\d[\d\s().-]{5,}\d(?![\w])")
# roll numbers / student ids such as 21BCE1234 (letters and digits mixed, 7+ characters)
STUDENT_ID = re.compile(r"\b(?=[A-Za-z0-9]*\d)(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{7,}\b")


def _hide_number(match):
    digits = sum(ch.isdigit() for ch in match.group())
    return "[number removed]" if digits >= 7 else match.group()


def clean_comment(text):
    """Remove emails, links, @handles, phone numbers and student ids from a comment."""
    if not text:
        return None
    text = EMAIL.sub("[email removed]", text)
    text = LINK.sub("[link removed]", text)
    text = HANDLE.sub("[handle removed]", text)
    text = PHONE.sub(_hide_number, text)
    text = STUDENT_ID.sub("[id removed]", text)
    text = " ".join(text.split())
    return text or None