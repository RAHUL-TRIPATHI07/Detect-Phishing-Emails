from src.preprocessing import (
    extract_email_content,
)


def test_plain_text_email():

    raw_email = b"""\
From: sender@example.com
To: receiver@example.com
Subject: Test Email
Content-Type: text/plain; charset="utf-8"

Hello,

This is a test email.
"""

    subject, body = extract_email_content(raw_email)

    assert subject == "Test Email"
    assert "This is a test email." in body


def test_html_email():

    raw_email = b"""\
From: sender@example.com
To: receiver@example.com
Subject: HTML Test
Content-Type: text/html; charset="utf-8"

<html>
    <head>
        <style>
            body { color: red; }
        </style>
    </head>

    <body>
        <h1>Welcome!</h1>
        <p>This is an <strong>HTML email</strong>.</p>

        <script>
            alert("This should not appear");
        </script>
    </body>
</html>
"""

    subject, body = extract_email_content(raw_email)

    assert subject == "HTML Test"
    assert "Welcome!" in body
    assert "HTML email" in body

    # JavaScript and CSS should not survive extraction
    assert "alert(" not in body
    assert "color: red" not in body


def test_empty_subject():

    raw_email = b"""\
From: sender@example.com
To: receiver@example.com
Content-Type: text/plain; charset="utf-8"

Body without a subject.
"""

    subject, body = extract_email_content(raw_email)

    assert subject == ""
    assert "Body without a subject." in body


def test_invalid_input_type():

    try:
        extract_email_content("not bytes")
        assert False
    except TypeError:
        assert True