"""
Email scanning pipeline.

Takes raw email messages and runs them through
the existing Spam + Phishing prediction pipeline.
"""

from src.predict import EmailSecurityPredictor


class EmailScanner:

    def __init__(self, predictor=None):
        """
        Initialize the email scanner.

        Args:
            predictor: Optional EmailSecurityPredictor instance.
        """

        self.predictor = predictor or EmailSecurityPredictor()

    @staticmethod
    def determine_category(spam_decision, phishing_decision):
        """
        Determine the user-facing email category.

        This is not a third ML classifier.
        It is derived from the two independent model decisions.
        """

        if spam_decision == "SPAM" and phishing_decision == "PHISHING":
            return "BOTH"

        if spam_decision == "SPAM":
            return "SPAM"

        if spam_decision == "MAYBE SPAM":
            return "MAYBE SPAM"

        if phishing_decision == "PHISHING":
            return "PHISHING"

        return "NONE"

    def scan_messages(self, messages):
        """
        Scan a collection of raw email messages.

        Args:
            messages: List of dictionaries containing:
                      - message_id
                      - thread_id
                      - subject
                      - sender
                      - date
                      - raw_bytes

        Returns:
            List of scan results.
        """

        if not isinstance(messages, list):
            raise TypeError("messages must be a list.")

        results = []

        for message in messages:

            message_id = message.get("message_id")
            raw_bytes = message.get("raw_bytes")

            if not message_id:
                continue

            if raw_bytes is None:
                results.append({
                    "message_id": message_id,
                    "status": "error",
                    "error": message.get(
                        "error",
                        "Raw email data is unavailable."
                    )
                })
                continue

            try:
                prediction = self.predictor.predict_raw_email(
                    raw_bytes
                )

                category = self.determine_category(
                    prediction["spam_decision"],
                    prediction["phishing_decision"]
                )

                results.append({
                    "message_id": message_id,
                    "thread_id": message.get("thread_id"),
                    "subject": message.get("subject", ""),
                    "sender": message.get("sender", ""),
                    "date": message.get("date", ""),
                    "status": "success",
                    "category": category,
                    "spam_score": prediction["spam_score"],
                    "spam_decision": prediction["spam_decision"],
                    "phishing_score": prediction["phishing_score"],
                    "phishing_decision": prediction["phishing_decision"],
                    "risk_level": prediction["risk_level"],
                    "reasons": prediction["reasons"]
                })

            except Exception as exc:
                results.append({
                    "message_id": message_id,
                    "thread_id": message.get("thread_id"),
                    "subject": message.get("subject", ""),
                    "sender": message.get("sender", ""),
                    "date": message.get("date", ""),
                    "status": "error",
                    "error": str(exc)
                })

        return results

    @staticmethod
    def summarize_results(results):
        """
        Create a summary of scan results.
        """

        summary = {
            "total": len(results),
            "successful": 0,
            "errors": 0,
            "spam": 0,
            "maybe_spam": 0,
            "phishing": 0,
            "both": 0,
            "none": 0
        }

        for item in results:

            if item.get("status") != "success":
                summary["errors"] += 1
                continue

            summary["successful"] += 1

            category = item.get("category")

            if category == "BOTH":
                summary["both"] += 1

            elif category == "SPAM":
                summary["spam"] += 1

            elif category == "MAYBE SPAM":
                summary["maybe_spam"] += 1

            elif category == "PHISHING":
                summary["phishing"] += 1

            elif category == "NONE":
                summary["none"] += 1

        return summary