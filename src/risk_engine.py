"""
Risk Engine for Intelligent Email Security Detection.

Combines independent Spam and Phishing model outputs
into a transparent, rule-based risk assessment.
"""

# Spam decision boundaries
SPAM_MAYBE_THRESHOLD = 0.47
SPAM_HIGH_THRESHOLD = 0.65

# Phishing decision threshold
PHISHING_THRESHOLD = 0.50


def classify_spam(score):
    """
    Convert the Spam model score into a three-zone decision.

    Returns:
        NOT SPAM
        MAYBE SPAM
        SPAM
    """

    if score < SPAM_MAYBE_THRESHOLD:
        return "NOT SPAM"

    elif score < SPAM_HIGH_THRESHOLD:
        return "MAYBE SPAM"

    else:
        return "SPAM"


def classify_phishing(score):
    """
    Convert the Phishing model score into a binary decision.

    Returns:
        NOT PHISHING
        PHISHING
    """

    if score >= PHISHING_THRESHOLD:
        return "PHISHING"

    return "NOT PHISHING"



def assess_risk(spam_score, phishing_score):
    """
    Combine Spam and Phishing model decisions
    into an overall risk assessment.

    Returns:
        dict containing model decisions and risk level.
    """

    spam_decision = classify_spam(spam_score)
    phishing_decision = classify_phishing(phishing_score)

    # Both models identify the email as suspicious
    if (
        spam_decision == "NOT SPAM"
        and phishing_decision == "NOT PHISHING"
    ):
        risk_level = "LOW"

    # NOT SPAM + PHISHING
    elif (
        spam_decision == "NOT SPAM"
        and phishing_decision == "PHISHING"
    ):
        risk_level = "HIGH"

    # MAYBE SPAM + NOT PHISHING
    elif (
        spam_decision == "MAYBE SPAM"
        and phishing_decision == "NOT PHISHING"
    ):
        risk_level = "MEDIUM"

    # MAYBE SPAM + PHISHING
    elif (
        spam_decision == "MAYBE SPAM"
        and phishing_decision == "PHISHING"
    ):
        risk_level = "MEDIUM-HIGH"

    # SPAM + NOT PHISHING
    elif (
        spam_decision == "SPAM"
        and phishing_decision == "NOT PHISHING"
    ):
        risk_level = "MEDIUM"

    # SPAM + PHISHING
    elif (
        spam_decision == "SPAM"
        and phishing_decision == "PHISHING"
    ):
        risk_level = "HIGH"

    else:
        raise ValueError("Unexpected Spam/Phishing decision combination")


    reasons = generate_reasons(
        spam_score,
        spam_decision,
        phishing_score,
        phishing_decision
    )

        

    return {
        "spam_score": spam_score,
        "spam_decision": spam_decision,
        "phishing_score": phishing_score,
        "phishing_decision": phishing_decision,
        "risk_level": risk_level,
        "reasons": reasons
    }


def generate_reasons(
    spam_score,
    spam_decision,
    phishing_score,
    phishing_decision
):
    """
    Generate human-readable explanations
    for the model decisions.
    """

    reasons = []

    # Spam explanation
    if spam_decision == "SPAM":
        reasons.append(
            f"Spam model score ({spam_score:.4f}) is above "
            f"the high-confidence spam boundary ({SPAM_HIGH_THRESHOLD:.2f})."
        )

    elif spam_decision == "MAYBE SPAM":
        reasons.append(
            f"Spam model score ({spam_score:.4f}) falls within "
            f"the uncertain range "
            f"({SPAM_MAYBE_THRESHOLD:.2f}–{SPAM_HIGH_THRESHOLD:.2f})."
        )

    else:
        reasons.append(
            f"Spam model score ({spam_score:.4f}) is below "
            f"the spam decision boundary ({SPAM_MAYBE_THRESHOLD:.2f})."
        )

    # Phishing explanation
    if phishing_decision == "PHISHING":
        reasons.append(
            f"Phishing model score ({phishing_score:.4f}) is at or above "
            f"the phishing threshold ({PHISHING_THRESHOLD:.2f})."
        )

    else:
        reasons.append(
            f"Phishing model score ({phishing_score:.4f}) is below "
            f"the phishing threshold ({PHISHING_THRESHOLD:.2f})."
        )

    # Model relationship
    if (
        spam_decision == "SPAM"
        and phishing_decision == "PHISHING"
    ):
        reasons.append(
            "Both independent security models flagged the email."
        )

    elif (
        spam_decision == "SPAM"
        and phishing_decision == "NOT PHISHING"
    ):
        reasons.append(
            "The email is flagged as spam-like, but the "
            "phishing model did not cross its decision threshold."
        )

    elif (
        spam_decision == "MAYBE SPAM"
        and phishing_decision == "PHISHING"
    ):
        reasons.append(
            "Phishing was detected, while the spam signal "
            "remains borderline."
        )

    elif (
        spam_decision == "NOT SPAM"
        and phishing_decision == "PHISHING"
    ):
        reasons.append(
            "The email is not classified as spam, but the "
            "phishing model detected a phishing signal."
        )

    else:
        reasons.append(
            "Neither model produced a strong combined warning."
        )

    return reasons