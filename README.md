# 🛡️ Sentinel AI — Intelligent Email Security Detection & Risk Analysis

> **A production-oriented machine learning system that independently detects phishing and spam emails, quantifies risk, and provides actionable security decisions through a deployed web application with Gmail integration.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi\&logoColor=white)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikit-learn\&logoColor=white)](https://scikit-learn.org/)
[![Gmail API](https://img.shields.io/badge/Gmail-API-EA4335?logo=gmail\&logoColor=white)](https://developers.google.com/gmail/api)
[![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?logo=render\&logoColor=white)](https://render.com/)

---

## 🚀 Live Application



### **Sentinel AI**

**https://sentinel-ygyk.onrender.com/**

The application provides a web interface for:

* Manual email analysis
* Spam probability estimation
* Phishing probability estimation
* Combined security-risk assessment
* Gmail authentication
* Gmail message retrieval
* Email scanning through the deployed API

> **Gmail access note:** Gmail integration uses Google's OAuth authorization flow and requests `gmail.readonly`. Public unrestricted Gmail access requires Google's verification process for restricted scopes. The deployed application therefore should not be represented as an unrestricted public Gmail security service.

---

# 📌 Table of Contents

* [Overview](#-overview)
* [Problem Statement](#-problem-statement)
* [Key Design Decision](#-key-design-decision)
* [System Architecture](#-system-architecture)
* [How the System Works](#-how-the-system-works)
* [Machine Learning Pipeline](#-machine-learning-pipeline)
* [Phishing Detection Model](#-phishing-detection-model)
* [Spam Detection Model](#-spam-detection-model)
* [Risk Engine](#-risk-engine)
* [Datasets](#-datasets)
* [Data Leakage Prevention](#-data-leakage-prevention)
* [Evaluation Strategy](#-evaluation-strategy)
* [Final Model Performance](#-final-model-performance)
* [Error Analysis](#-error-analysis)
* [Gmail Integration](#-gmail-integration)
* [Security & Privacy](#-security--privacy)
* [Project Structure](#-project-structure)
* [Tech Stack](#-tech-stack)
* [Local Setup](#-local-setup)
* [Environment Variables](#-environment-variables)
* [Running the Application](#-running-the-application)
* [API Endpoints](#-api-endpoints)
* [Testing](#-testing)
* [Deployment](#-deployment)
* [Limitations](#-limitations)
* [Future Improvements](#-future-improvements)
* [What This Project Demonstrates](#-what-this-project-demonstrates)
* [License](#-license)

---

# 🔎 Overview

**Sentinel AI** is an intelligent email security system designed to analyze email content and identify two different types of threats:

1. **Spam**
2. **Phishing**

Instead of treating email security as a single classification problem, Sentinel AI uses **two independent binary machine learning classifiers**.

```text
                         ┌─────────────────────┐
                         │        EMAIL        │
                         │ Subject + Body      │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          ┌─────────────────┐             ┌─────────────────┐
          │ PHISHING MODEL  │             │   SPAM MODEL    │
          │ Logistic Reg.   │             │ Logistic Reg.  │
          └────────┬────────┘             └────────┬────────┘
                   │                               │
                   ▼                               ▼
          Phishing Probability               Spam Probability
                   │                               │
                   └───────────────┬───────────────┘
                                   ▼
                         ┌─────────────────────┐
                         │    RISK ENGINE      │
                         │                     │
                         │ Decisions + Reasons │
                         └──────────┬──────────┘
                                    │
                                    ▼
                           Final Risk Assessment
```

This architecture allows an email to be:

* Not spam but phishing
* Spam but not phishing
* Both spam and phishing
* Neither spam nor phishing

That distinction is important because **spam and phishing represent different security concepts**.

---

# 🎯 Problem Statement

Traditional email filtering often focuses primarily on whether a message is spam.

However, a phishing email can be dangerous even when it does not look like conventional bulk spam.

For example:

```text
Spam:
Promotional / unwanted email

Phishing:
An email attempting to deceive the recipient into revealing
credentials, clicking a malicious link, transferring money,
or taking another harmful action.
```

Therefore, the system separates the two tasks:

### Spam Detection

> "Is this email likely to be unwanted/spam?"

### Phishing Detection

> "Does this email contain characteristics associated with phishing?"

The outputs are then combined by a deterministic risk engine.

---

# 🧠 Key Design Decision

## Why two independent models?

A single three-class classifier such as:

```text
LEGITIMATE
SPAM
PHISHING
```

was intentionally **not used**.

Instead:

```text
Email
 ├── Spam Classifier
 └── Phishing Classifier
```

Both models independently produce probabilities.

This allows:

```text
Spam probability     = 0.91
Phishing probability = 0.87
```

to produce:

```text
SPAM + PHISHING
```

rather than forcing the email into one mutually exclusive class.

This is a more appropriate representation of the underlying security problem.

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │      Frontend       │
                         │    Sentinel AI      │
                         └──────────┬──────────┘
                                    │
                                    │ HTTPS
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │       Backend       │
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
        ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
        │ Gmail OAuth  │    │ Email Parser │    │ ML Inference │
        └──────────────┘    └──────────────┘    └──────┬───────┘
                                                       │
                                     ┌─────────────────┴─────────────────┐
                                     │                                   │
                                     ▼                                   ▼
                             ┌───────────────┐                   ┌───────────────┐
                             │    Spam       │                   │   Phishing    │
                             │    Model      │                   │    Model      │
                             └───────┬───────┘                   └───────┬───────┘
                                     │                                   │
                                     └────────────────┬──────────────────┘
                                                      ▼
                                             ┌─────────────────┐
                                             │   Risk Engine   │
                                             └────────┬────────┘
                                                      ▼
                                             Security Assessment
```

---

# ⚙️ How the System Works

## 1. Email ingestion

The system accepts:

* Subject
* Body
* Raw MIME email

For Gmail messages, raw email content is retrieved through the Gmail API.

---

## 2. Email preprocessing

The preprocessing layer:

* Parses MIME email structures
* Extracts the subject
* Extracts plain-text content when available
* Falls back to visible HTML text when necessary
* Removes irrelevant HTML structure
* Ignores attachments for text classification
* Validates basic email content

The same preprocessing/inference path is used before sending content to the models.

---

## 3. Feature extraction

Email text is transformed using **TF-IDF**.

The phishing model uses:

```text
TF-IDF
ngram_range = (1, 2)
```

The spam model uses:

```text
TF-IDF
ngram_range = (1, 1)
```

The vectorizers are fitted only on the appropriate training data and persisted with the trained models.

---

## 4. Machine learning inference

Each model independently generates:

```text
P(phishing)
P(spam)
```

These probabilities are passed to the risk engine.

---

## 5. Risk assessment

The risk engine converts the probabilities into interpretable decisions.

Example:

```text
Spam score:      0.82
Phishing score:  0.91

Spam decision:       SPAM
Phishing decision:   PHISHING

Final risk:          HIGH
```

---

# 🤖 Machine Learning Pipeline

The overall training workflow is:

```text
Raw Dataset
     │
     ▼
Data Inspection
     │
     ▼
Cleaning & Normalization
     │
     ▼
Duplicate / Group Analysis
     │
     ▼
Group-Aware Train / Validation / Test Split
     │
     ├───────────────┐
     ▼               ▼
Train             Validation
     │               │
     ▼               ▼
TF-IDF            Threshold
     │             Selection
     ▼               │
Logistic Regression │
     │               │
     └───────┬───────┘
             ▼
      Final Evaluation
       on Held-Out Test
```

---

# 🎣 Phishing Detection Model

## Dataset

The phishing classifier was trained using the **MeAJOR phishing email dataset**.

Source:

**Zenodo — MeAJOR Phishing Dataset**

https://zenodo.org/records/18471483

Initial dataset:

```text
108,685 rows
20 columns
```

After cleaning:

```text
108,671 emails
```

---

## Data splitting

The dataset was split using SHA-256 hashes derived from:

```text
subject + body
```

This created groups of identical email content.

Final split:

| Split      |     Samples |
| ---------- | ----------: |
| Train      |      86,933 |
| Validation |      10,976 |
| Test       |      10,762 |
| **Total**  | **108,671** |

There were **no group intersections between train, validation, and test sets**.

---

## Model selection

A unigram Logistic Regression baseline was first evaluated.

### Unigram baseline

```text
Features: 96,955
```

Validation:

| Metric    |    Score |
| --------- | -------: |
| Precision | 0.973548 |
| Recall    | 0.976373 |
| F1        | 0.974959 |
| ROC-AUC   | 0.996835 |
| PR-AUC    | 0.995992 |

A controlled bigram experiment was then performed.

### Unigram + Bigram

```text
Features: 882,481
```

Validation:

| Metric    |    Score |
| --------- | -------: |
| Precision | 0.980849 |
| Recall    | 0.976580 |
| F1        | 0.978710 |
| ROC-AUC   | 0.997598 |
| PR-AUC    | 0.996998 |

The `(1,2)` configuration was selected.

---

## Final held-out phishing performance

The final model was evaluated on the previously untouched test set.

| Metric        |        Score |
| ------------- | -----------: |
| **Precision** | **0.978265** |
| **Recall**    | **0.975640** |
| **F1 Score**  | **0.976951** |
| **ROC-AUC**   | **0.997696** |
| **PR-AUC**    | **0.997051** |

Confusion matrix:

```text
                 Predicted
               Legit  Phish
Actual Legit    5813    105
Actual Phish     118   4726
```

The operating threshold selected from validation was:

```text
Phishing threshold = 0.50
```

The test set was not used for threshold tuning.

---

# 📨 Spam Detection Model

## Dataset

The spam classifier uses the classic **SpamAssassin Public Corpus**.

Source:

https://spamassassin.apache.org/old/publiccorpus/

Dataset composition:

| Category  |    Emails |
| --------- | --------: |
| HAM       |     2,752 |
| SPAM      |       501 |
| **Total** | **3,253** |

Class distribution:

```text
HAM  = 84.60%
SPAM = 15.40%
```

Because of this imbalance, class weighting was investigated.

---

## Email extraction

The SpamAssassin corpus contains MIME emails.

The extraction pipeline uses Python's email parsing facilities and BeautifulSoup to obtain useful text.

The following were intentionally excluded from model text:

* `X-Spam` classification headers
* Raw infrastructure headers
* Attachments

This helps prevent the model from learning dataset-generated labels or infrastructure artifacts.

---

## Group-aware splitting

Duplicate Subject + Body groups were identified before splitting.

Final grouped split:

| Split      |    Groups |
| ---------- | --------: |
| Train      |     2,271 |
| Validation |       489 |
| Test       |       493 |
| **Total**  | **3,205** |

No group intersections were present across the three splits.

---

## Model selection

The selected model is:

```text
TF-IDF
    +
Logistic Regression
    +
class_weight="balanced"
```

The model uses word-level unigram features.

The selected binary operating threshold is:

```text
0.47
```

---

# 📊 Final Spam Performance

The final model was retrained on the combined training + validation data and evaluated once on the held-out test set.

Training data:

```text
2,760 emails
2,336 HAM
424 SPAM
```

Held-out test data:

```text
493 emails
416 HAM
77 SPAM
```

Final vocabulary:

```text
21,096 features
```

### Test Performance

| Metric        |        Score |
| ------------- | -----------: |
| **Precision** | **0.884615** |
| **Recall**    | **0.896104** |
| **F1 Score**  | **0.890323** |
| **ROC-AUC**   | **0.995130** |
| **PR-AUC**    | **0.975340** |
| Accuracy      |      ~96.55% |

Confusion matrix:

```text
                 Predicted
                HAM   SPAM
Actual HAM      407     9
Actual SPAM       8    69
```

---

# 🎚️ Spam Decision Zones

The spam model produces a probability between `0` and `1`.

Sentinel AI uses three decision zones:

```text
Score < 0.47
        ↓
    NOT SPAM

0.47 ≤ Score < 0.65
        ↓
   MAYBE SPAM

Score ≥ 0.65
        ↓
      SPAM
```

Important distinction:

```text
0.47 = binary model decision threshold

0.65 = high-confidence / decision-zone boundary
```

The binary model threshold is **not** overwritten by `0.65`.

---

# 🧮 Risk Engine

The risk engine combines the independent spam and phishing decisions.

## Decision Matrix

|                | NOT PHISHING | PHISHING       |
| -------------- | ------------ | -------------- |
| **NOT SPAM**   | 🟢 LOW       | 🔴 HIGH        |
| **MAYBE SPAM** | 🟡 MEDIUM    | 🟠 MEDIUM-HIGH |
| **SPAM**       | 🟡 MEDIUM    | 🔴 HIGH        |

Examples:

### Case 1 — Clean

```text
Spam:      0.12 → NOT SPAM
Phishing:  0.08 → NOT PHISHING

Risk: LOW
```

### Case 2 — Phishing without spam

```text
Spam:      0.21 → NOT SPAM
Phishing:  0.83 → PHISHING

Risk: HIGH
```

### Case 3 — Suspicious spam

```text
Spam:      0.54 → MAYBE SPAM
Phishing:  0.19 → NOT PHISHING

Risk: MEDIUM
```

### Case 4 — Both

```text
Spam:      0.91 → SPAM
Phishing:  0.94 → PHISHING

Risk: HIGH
```

---

# 🔐 Data Leakage Prevention

Data leakage was treated as a first-class concern during model development.

### Measures used

#### 1. Group-aware splitting

Duplicate or near-identical email content was grouped before splitting.

This prevents copies of the same message from appearing in both training and evaluation data.

#### 2. TF-IDF fitted only on training data

The vectorizer is not fitted on the test set.

```text
Training:
fit_transform()

Validation/Test:
transform()
```

#### 3. Test set remains untouched

The held-out test set is used only for final evaluation.

Threshold selection and model decisions are based on validation data.

#### 4. Dataset-generated spam headers excluded

SpamAssassin `X-Spam` headers and related infrastructure information were excluded to avoid giving the classifier direct access to dataset labels.

---

# 🧪 Evaluation Strategy

Accuracy alone is not sufficient for security classification.

The project therefore evaluates:

* Precision
* Recall
* F1 Score
* ROC-AUC
* PR-AUC
* Confusion Matrix
* Error Analysis

### Why these metrics?

**Precision**

> When the model flags an email, how often is it actually positive?

**Recall**

> How many actual malicious/spam messages did the model identify?

**F1**

> How well does the model balance precision and recall?

**ROC-AUC**

> How well does the model rank positive examples above negative examples?

**PR-AUC**

> How well does the model perform under class imbalance and for the positive class?

---

# 🔬 Error Analysis

Model evaluation did not stop at aggregate metrics.

The spam validation errors included false negatives involving **Chinese promotional spam**.

This revealed an important limitation:

> Word-level TF-IDF can struggle with multilingual or linguistically different spam patterns when the training corpus does not adequately represent them.

This is treated as a modeling limitation rather than hidden through arbitrary test-set tuning.

Potential future solutions include:

* Character n-grams
* Multilingual embeddings
* Transformer-based models
* Language-aware preprocessing
* Multilingual training data

---

# 📧 Gmail Integration

Sentinel AI supports Gmail authorization through Google's OAuth 2.0 flow.

The application requests:

```text
https://www.googleapis.com/auth/gmail.readonly
```

This allows the application to read authorized Gmail messages without requesting permission to send, delete, or modify mail.

### OAuth Flow

```text
User
  │
  ▼
Sentinel AI
  │
  ▼
Google OAuth
  │
  ▼
User grants permission
  │
  ▼
OAuth callback
  │
  ▼
Session established
  │
  ▼
Gmail API
  │
  ▼
Retrieve email
  │
  ▼
Sentinel AI
  │
  ├── Spam Model
  ├── Phishing Model
  └── Risk Engine
```

The application uses the Gmail API's `getProfile` endpoint to identify the authorized Gmail account.

---

# 🔒 Security & Privacy

Security considerations were incorporated into the application architecture.

### Implemented

* HTTPS-only production sessions
* Cross-origin credentials configured explicitly
* Environment-based OAuth configuration
* OAuth client secret stored outside source code
* Session secret stored in environment variables
* Production token encryption key configuration
* Gmail `readonly` scope
* Consent checkbox before Gmail connection
* Privacy Policy
* Terms & Conditions

### Secrets

Credentials should **never** be committed to Git.

Examples:

```text
GOOGLE_CLIENT_SECRET
SESSION_SECRET_KEY
TOKEN_ENCRYPTION_KEY
```

are configured through environment variables.

---

# 📁 Project Structure

```text
Detect-Phishing-Emails/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── 01_phishing_dataset.ipynb
│   ├── 02_phishing_model.ipynb
│   ├── 03_spam_dataset.ipynb
│   └── 04_spam_model.ipynb
│
├── src/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── features.py
│   ├── train_phishing.py
│   ├── train_spam.py
│   ├── predict.py
│   ├── risk_engine.py
│   ├── scanner.py
│   ├── config.py
│   ├── session.py
│   ├── oauth_storage.py
│   └── connectors/
│       └── gmail.py
│
├── models/
│   ├── phishing_model.joblib
│   └── spam_model.joblib
│
├── app/
│   └── api.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   ├── privacy.html
│   └── terms.html
│
├── tests/
│   ├── __init__.py
│   ├── test_preprocessing.py
│   ├── test_risk_engine.py
│   └── test_predict.py
│
├── requirements.txt
├── render.yaml
├── .gitignore
└── README.md
```

---

# 🛠️ Tech Stack

## Machine Learning

* Python
* scikit-learn
* Logistic Regression
* TF-IDF
* NumPy
* pandas
* joblib

## NLP

* Text preprocessing
* MIME email parsing
* HTML extraction
* TF-IDF vectorization
* Word n-grams

## Backend

* FastAPI
* Uvicorn
* Pydantic
* Starlette Sessions

## Email Integration

* Gmail API
* Google OAuth 2.0

## Frontend

* HTML5
* CSS3
* JavaScript
* Responsive UI

## Deployment

* Render
* Environment-based configuration
* HTTPS

---

# 💻 Local Setup

## 1. Clone the repository

```bash
git clone https://github.com/RAHUL-TRIPATHI07/Detect-Phishing-Emails.git
cd Detect-Phishing-Emails
```

---

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create:

```text
.env
```

Example:

```env
ENVIRONMENT=development

SESSION_SECRET_KEY=your_session_secret

FRONTEND_URL=http://127.0.0.1:5500

GMAIL_REDIRECT_URI=http://127.0.0.1:8000/auth/gmail/callback

GOOGLE_CLIENT_ID=your_google_client_id

GOOGLE_CLIENT_SECRET=your_google_client_secret

DATABASE_URL=sqlite:///./sentinel.db

TOKEN_ENCRYPTION_KEY=your_token_encryption_key
```

**Never commit `.env` or OAuth secrets.**

---

# ▶️ Running the Backend

From the project root:

```bash
uvicorn app.api:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

Expected:

```json
{
  "status": "ok"
}
```

---

# 🌐 Running the Frontend

Serve the `frontend/` directory using a local static server.

For example:

```bash
python -m http.server 5500 --directory frontend
```

Then open:

```text
http://127.0.0.1:5500
```

---

# 🔌 API Endpoints

The FastAPI backend exposes endpoints for:

| Endpoint                                   | Purpose                        |
| ------------------------------------------ | ------------------------------ |
| `GET /health`                              | Health check                   |
| `POST /predict`                            | Analyze an email               |
| `GET /auth/gmail`                          | Start Gmail OAuth              |
| `GET /auth/gmail/callback`                 | OAuth callback                 |
| `GET /auth/gmail/status`                   | Check Gmail connection         |
| `GET /gmail/messages`                      | Retrieve Gmail messages        |
| `GET /gmail/messages/{message_id}/raw`     | Retrieve raw email             |
| `GET /gmail/messages/{message_id}/predict` | Predict individual Gmail email |
| `GET /gmail/scan`                          | Scan Gmail messages            |

---

# 🧪 Testing

The project includes tests covering important components such as:

* Email preprocessing
* Risk engine logic
* Prediction behavior

Run:

```bash
pytest
```

The goal is to ensure that changes to the application do not silently alter core security decisions.

---

# ☁️ Deployment

The backend is deployed using Render.

Production architecture:

```text
                 Internet
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   Sentinel Frontend      FastAPI Backend
       Render                Render
          │                   │
          └─────────┬─────────┘
                    │
                    ▼
                Gmail API
```

The production backend uses environment variables for:

* Google OAuth credentials
* Session secrets
* Token encryption
* Frontend origin
* OAuth callback URL
* Runtime environment

---

# ⚠️ Limitations

Sentinel AI is a machine-learning based detection system and **not a guarantee of maliciousness or safety**.

### Current limitations include:

#### 1. Content-based classification

The current ML models primarily use email textual content.

They do not fully analyze:

* URL reputation
* Domain age
* DNS records
* Sender authentication
* SPF
* DKIM
* DMARC
* Attachment malware
* Browser behavior
* Threat-intelligence feeds

#### 2. Multilingual detection

The SpamAssassin training corpus is relatively limited compared with real-world global email traffic.

Performance may therefore vary for languages and writing styles that are poorly represented in the training data.

#### 3. Dataset shift

Real-world phishing and spam campaigns evolve continuously.

A model trained on historical datasets can encounter patterns that were not present during training.

#### 4. ML score ≠ proof

A high phishing probability means:

> The email resembles phishing examples learned by the classifier.

It does **not** independently prove that the sender or message is malicious.

---

# 🔮 Future Improvements

Potential production extensions include:

### Threat intelligence

Integrate:

* URL reputation services
* Domain reputation
* IP reputation
* Threat intelligence feeds

### Authentication analysis

Add:

```text
SPF
DKIM
DMARC
Return-Path
From-domain alignment
Reply-To anomalies
```

### URL analysis

Extract and analyze:

```text
URLs
Domain age
Redirect chains
HTTPS configuration
Lookalike domains
Punycode
URL entropy
```

### Advanced NLP

Experiment with:

* Character n-grams
* Multilingual embeddings
* Sentence Transformers
* BERT-style models
* Fine-tuned transformer classifiers

### Explainability

Provide:

```text
Why was this email flagged?
```

using:

* Important terms
* Model coefficients
* SHAP/LIME-style explanations
* Suspicious URL indicators
* Sender anomalies

### Continuous learning

Build a feedback loop:

```text
Prediction
    ↓
User Feedback
    ↓
Verified Label
    ↓
Training Dataset
    ↓
Model Evaluation
    ↓
Controlled Retraining
```

with strict safeguards against poisoning and leakage.

### Production security

Future versions could add:

* Rate limiting
* Authentication for application users
* Audit logging
* Secret rotation
* Stronger token storage
* Monitoring
* Model drift detection
* Abuse prevention

---

# 📈 Project Highlights

## Phishing Classifier

```text
F1 Score      97.70%
ROC-AUC       99.77%
PR-AUC        99.71%
Precision     97.83%
Recall        97.56%
```

## Spam Classifier

```text
F1 Score      89.03%
ROC-AUC       99.51%
PR-AUC        97.53%
Precision     88.46%
Recall        89.61%
```

These are **held-out test-set results**, not training-set metrics.

---

# 🧠 Engineering Principles

This project was developed around several principles:

### 1. Separate the ML problems

Spam and phishing are modeled independently.

### 2. Prevent data leakage

Group-aware splitting and train-only TF-IDF fitting are used.

### 3. Keep the test set untouched

Model and threshold decisions are made using training/validation data.

### 4. Prefer interpretable models

Logistic Regression provides a strong baseline while remaining relatively interpretable.

### 5. Evaluate beyond accuracy

Precision, recall, F1, ROC-AUC, PR-AUC and error analysis are considered.

### 6. Separate prediction from policy

The ML models produce probabilities.

The deterministic risk engine converts those probabilities into application-level decisions.

```text
ML
 ↓
Probability
 ↓
Decision Policy
 ↓
Risk Level
```

This separation makes the system easier to test, tune, and evolve.

---

# 🎓 What This Project Demonstrates

This project goes beyond training a classifier.

It demonstrates experience with:

* End-to-end ML development
* NLP
* Binary classification
* Logistic Regression
* TF-IDF
* Imbalanced classification
* Threshold selection
* Group-aware dataset splitting
* Data leakage prevention
* Model evaluation
* Error analysis
* Model persistence
* Production inference
* FastAPI
* REST APIs
* Gmail API
* OAuth 2.0
* Session management
* Environment-based configuration
* Frontend/backend integration
* Deployment
* Security and privacy considerations
* Software testing
* ML system architecture

---

# 📚 Dataset Sources

### MeAJOR Phishing Dataset

Zenodo:

https://zenodo.org/records/18471483

Used for phishing classification.

### SpamAssassin Public Corpus

SpamAssassin:

https://spamassassin.apache.org/old/publiccorpus/

Used for spam classification.

Please review and comply with the respective dataset licenses and usage conditions when redistributing or extending the project.

---

# 👨‍💻 Author

**Rahul Tripathi**

GitHub:

https://github.com/RAHUL-TRIPATHI07

Project Repository:

https://github.com/RAHUL-TRIPATHI07/Detect-Phishing-Emails

---

# ⭐ If You Find This Project Interesting

If this project helped you understand practical NLP, email security, or ML system design, consider giving the repository a ⭐.

---

## ⚖️ Disclaimer

Sentinel AI is an experimental/portfolio-oriented email security system.

Its predictions are probabilistic and should not be treated as definitive proof that an email is malicious, safe, spam, or legitimate.

Users should independently verify suspicious communications and should not rely solely on automated classification for security-critical decisions.

---




