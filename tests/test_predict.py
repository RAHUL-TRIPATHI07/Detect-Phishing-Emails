import pytest

from src.predict import EmailSecurityPredictor


@pytest.fixture(scope="module")
def predictor():

    return EmailSecurityPredictor()


def test_predictor_initialization(predictor):

    assert predictor.phishing_bundle is not None
    assert predictor.spam_bundle is not None


def test_model_bundles(predictor):

    assert "vectorizer" in predictor.phishing_bundle
    assert "model" in predictor.phishing_bundle
    assert "threshold" in predictor.phishing_bundle

    assert "vectorizer" in predictor.spam_bundle
    assert "model" in predictor.spam_bundle
    assert "threshold" in predictor.spam_bundle


def test_frozen_thresholds(predictor):

    assert predictor.phishing_bundle["threshold"] == 0.50
    assert predictor.spam_bundle["threshold"] == 0.47


def test_predict_email(predictor):

    result = predictor.predict_email(
        subject="Test Email",
        body="This is a normal test email."
    )

    assert isinstance(result, dict)

    assert "spam_score" in result
    assert "spam_decision" in result

    assert "phishing_score" in result
    assert "phishing_decision" in result

    assert "risk_level" in result
    assert "reasons" in result


def test_score_ranges(predictor):

    result = predictor.predict_email(
        subject="Test Email",
        body="This is a normal test email."
    )

    assert 0.0 <= result["spam_score"] <= 1.0
    assert 0.0 <= result["phishing_score"] <= 1.0


def test_raw_email_prediction(predictor):

    raw_email = b"""\
From: sender@example.com
To: receiver@example.com
Subject: Test Email
Content-Type: text/plain; charset="utf-8"

Hello,

This is a test email.
"""

    result = predictor.predict_raw_email(raw_email)

    assert isinstance(result, dict)
    assert "spam_score" in result
    assert "phishing_score" in result
    assert "risk_level" in result


def test_empty_subject_and_body(predictor):

    with pytest.raises(ValueError):

        predictor.predict_email(
            subject="",
            body=""
        )


def test_invalid_subject_type(predictor):

    with pytest.raises(TypeError):

        predictor.predict_email(
            subject=None,
            body="Some body"
        )


def test_invalid_body_type(predictor):

    with pytest.raises(TypeError):

        predictor.predict_email(
            subject="Test",
            body=None
        )


def test_invalid_raw_email_type(predictor):

    with pytest.raises(TypeError):

        predictor.predict_raw_email(
            "not bytes"
        )