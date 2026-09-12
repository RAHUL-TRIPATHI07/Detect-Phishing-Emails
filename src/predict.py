"""
Inference pipeline for Intelligent Email Security Detection.

Loads the trained Spam and Phishing models and generates
security predictions for a new email.
"""

from pathlib import Path
import joblib

from src.risk_engine import assess_risk
from src.preprocessing import extract_email_content

class EmailSecurityPredictor:

    def __init__(self):
        """
        Initialize the inference pipeline and load both models.
        """

        project_root = Path(__file__).resolve().parent.parent
        model_dir = project_root / "models"

        self.phishing_model_path = model_dir / "phishing_model.joblib"
        self.spam_model_path = model_dir / "spam_model.joblib"

        self.phishing_bundle = self._load_model(
            self.phishing_model_path,
            "Phishing"
        )

        self.spam_bundle = self._load_model(
            self.spam_model_path,
            "Spam"
        )

    @staticmethod
    def _load_model(model_path, model_name):
        """
        Load a trained model bundle from disk.
        """

        if not model_path.exists():
            raise FileNotFoundError(
                f"{model_name} model not found: {model_path}"
            )

        return joblib.load(model_path)

    def predict_email(self, subject, body):
        """
        Run an email through both security models
        and the Risk Engine.

        Args:
            text (str): Email subject + body.

        Returns:
            dict: Complete security assessment.
        """

        if not isinstance(subject, str):
            raise TypeError("Subject must be a string.")

        if not isinstance(body, str):
            raise TypeError("Body must be a string.")

        if not subject.strip() and not body.strip():
            raise ValueError("Subject and body cannot both be empty.")

        # Combine subject and body in the same format
        # used during model training.
        text = (
            subject.strip()
            + " "
            + body.strip()
        ).strip()
        # Phishing model components
        phishing_vectorizer = self.phishing_bundle["vectorizer"]
        phishing_model = self.phishing_bundle["model"]

        # Spam model components
        spam_vectorizer = self.spam_bundle["vectorizer"]
        spam_model = self.spam_bundle["model"]

        # Transform using each model's own TF-IDF vectorizer
        phishing_features = phishing_vectorizer.transform([text])
        spam_features = spam_vectorizer.transform([text])

        # Model scores
        phishing_score = phishing_model.predict_proba(
            phishing_features
        )[0, 1]

        spam_score = spam_model.predict_proba(
            spam_features
        )[0, 1]

        # Risk Engine
        result = assess_risk(
            spam_score=spam_score,
            phishing_score=phishing_score
        )

        return result


    def predict_raw_email(self, raw_bytes):
        """
        Predict the security risk of a raw email message.

        Args:
            raw_bytes (bytes): Raw .eml email content.

        Returns:
            dict: Complete security assessment.
        """

        subject, body = extract_email_content(raw_bytes)

        result = self.predict_email(
            subject=subject,
            body=body
        )

        return result