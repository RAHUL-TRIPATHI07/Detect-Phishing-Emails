from src.risk_engine import (
    classify_spam,
    classify_phishing,
    assess_risk,
)


def test_spam_not_spam():
    assert classify_spam(0.20) == "NOT SPAM"


def test_spam_maybe():
    assert classify_spam(0.50) == "MAYBE SPAM"


def test_spam_spam():
    assert classify_spam(0.80) == "SPAM"


def test_phishing_not_phishing():
    assert classify_phishing(0.40) == "NOT PHISHING"


def test_phishing_phishing():
    assert classify_phishing(0.70) == "PHISHING"


def test_risk_not_spam_not_phishing():
    result = assess_risk(
        spam_score=0.20,
        phishing_score=0.40
    )

    assert result["spam_decision"] == "NOT SPAM"
    assert result["phishing_decision"] == "NOT PHISHING"
    assert result["risk_level"] == "LOW"


def test_risk_not_spam_phishing():
    result = assess_risk(
        spam_score=0.20,
        phishing_score=0.70
    )

    assert result["spam_decision"] == "NOT SPAM"
    assert result["phishing_decision"] == "PHISHING"
    assert result["risk_level"] == "HIGH"


def test_risk_maybe_spam_not_phishing():
    result = assess_risk(
        spam_score=0.50,
        phishing_score=0.40
    )

    assert result["spam_decision"] == "MAYBE SPAM"
    assert result["phishing_decision"] == "NOT PHISHING"
    assert result["risk_level"] == "MEDIUM"


def test_risk_maybe_spam_phishing():
    result = assess_risk(
        spam_score=0.50,
        phishing_score=0.70
    )

    assert result["spam_decision"] == "MAYBE SPAM"
    assert result["phishing_decision"] == "PHISHING"
    assert result["risk_level"] == "MEDIUM-HIGH"


def test_risk_spam_not_phishing():
    result = assess_risk(
        spam_score=0.80,
        phishing_score=0.40
    )

    assert result["spam_decision"] == "SPAM"
    assert result["phishing_decision"] == "NOT PHISHING"
    assert result["risk_level"] == "MEDIUM"


def test_risk_spam_phishing():
    result = assess_risk(
        spam_score=0.80,
        phishing_score=0.70
    )

    assert result["spam_decision"] == "SPAM"
    assert result["phishing_decision"] == "PHISHING"
    assert result["risk_level"] == "HIGH"


def test_spam_lower_boundary():
    assert classify_spam(0.47) == "MAYBE SPAM"


def test_spam_upper_boundary():
    assert classify_spam(0.65) == "SPAM"


def test_phishing_boundary():
    assert classify_phishing(0.50) == "PHISHING"