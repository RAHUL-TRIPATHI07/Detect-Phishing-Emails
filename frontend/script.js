const API_BASE_URL = "http://127.0.0.1:8000";

const connectGmailButton = document.getElementById("connect-gmail-btn");
const scanButton = document.getElementById("scan-btn");
const statusElement = document.getElementById("status");
const resultsBody = document.getElementById("results-body");

const emailModal = document.getElementById("email-modal");
const emailDetails = document.getElementById("email-details");
const closeModalButton = document.getElementById("close-modal-btn");

let scanResults = [];
let activeCategory = "ALL";


function setStatus(message) {
    statusElement.textContent = message;
}


function formatScore(score) {
    if (typeof score !== "number") {
        return "-";
    }

    return score.toFixed(3);
}


function getCategoryClass(category) {
    switch (category) {
        case "SPAM":
            return "badge-spam";

        case "MAYBE SPAM":
            return "badge-maybe";

        case "PHISHING":
            return "badge-phishing";

        case "BOTH":
            return "badge-both";

        default:
            return "badge-none";
    }
}


function getRiskClass(risk) {
    if (!risk) {
        return "";
    }

    return `risk-${risk.toLowerCase()}`;
}


function updateSummary(summary) {
    document.getElementById("total-count").textContent = summary.total;
    document.getElementById("spam-count").textContent = summary.spam;
    document.getElementById("maybe-spam-count").textContent =
        summary.maybe_spam;
    document.getElementById("phishing-count").textContent =
        summary.phishing;
    document.getElementById("both-count").textContent = summary.both;
    document.getElementById("none-count").textContent = summary.none;
}


function renderResults(results = scanResults) {

    resultsBody.innerHTML = "";

    const filteredResults = activeCategory === "ALL"
        ? results
        : results.filter(
            email => email.category === activeCategory
        );

    if (!filteredResults.length) {
        resultsBody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    No emails match this filter.
                </td>
            </tr>
        `;

        return;
    }

    filteredResults.forEach((email) => {

        const row = document.createElement("tr");

        if (email.status === "error") {

            row.innerHTML = `
                <td class="email-subject">
                    ${escapeHtml(email.subject || "Unknown email")}
                </td>

                <td>
                    -
                </td>

                <td>
                    <span class="badge badge-none">
                        ERROR
                    </span>
                </td>

                <td>-</td>
                <td>-</td>
                <td>-</td>
            `;

            resultsBody.appendChild(row);

            return;
        }


        row.innerHTML = `
            <td class="email-subject">
                ${escapeHtml(email.subject || "(No subject)")}
            </td>

            <td>
                ${escapeHtml(email.sender || "-")}
            </td>

            <td>
                <span class="badge ${getCategoryClass(email.category)}">
                    ${escapeHtml(email.category)}
                </span>
            </td>

            <td class="score">
                ${formatScore(email.spam_score)}
            </td>

            <td class="score">
                ${formatScore(email.phishing_score)}
            </td>

            <td class="${getRiskClass(email.risk_level)}">
                ${escapeHtml(email.risk_level)}
            </td>
        `;


        row.addEventListener(
            "click",
            () => showEmailDetails(email)
        );

        resultsBody.appendChild(row);
    });
}


function showEmailDetails(email) {

    emailDetails.innerHTML = `
        <div class="detail-row">
            <span>Subject</span>
            <strong>
                ${escapeHtml(email.subject || "(No subject)")}
            </strong>
        </div>

        <div class="detail-row">
            <span>Sender</span>
            <strong>
                ${escapeHtml(email.sender || "-")}
            </strong>
        </div>

        <div class="detail-row">
            <span>Date</span>
            <strong>
                ${escapeHtml(email.date || "-")}
            </strong>
        </div>

        <hr>

        <div class="detail-row">
            <span>Category</span>
            <span class="badge ${getCategoryClass(email.category)}">
                ${escapeHtml(email.category)}
            </span>
        </div>

        <div class="detail-row">
            <span>Spam Score</span>
            <strong>
                ${formatScore(email.spam_score)}
            </strong>
        </div>

        <div class="detail-row">
            <span>Spam Decision</span>
            <strong>
                ${escapeHtml(email.spam_decision || "-")}
            </strong>
        </div>

        <div class="detail-row">
            <span>Phishing Score</span>
            <strong>
                ${formatScore(email.phishing_score)}
            </strong>
        </div>

        <div class="detail-row">
            <span>Phishing Decision</span>
            <strong>
                ${escapeHtml(email.phishing_decision || "-")}
            </strong>
        </div>

        <div class="detail-row">
            <span>Risk Level</span>
            <strong class="${getRiskClass(email.risk_level)}">
                ${escapeHtml(email.risk_level || "-")}
            </strong>
        </div>

        <hr>

        <div class="reasons">
            <h3>Analysis</h3>

            <ul>
                ${
                    (email.reasons || [])
                        .map(
                            reason =>
                                `<li>${escapeHtml(reason)}</li>`
                        )
                        .join("")
                }
            </ul>
        </div>
    `;

    emailModal.classList.remove("hidden");
}


function closeEmailDetails() {
    emailModal.classList.add("hidden");
}


function escapeHtml(value) {

    const div = document.createElement("div");

    div.textContent = value;

    return div.innerHTML;
}


async function scanEmails() {

    scanButton.disabled = true;

    setStatus("Scanning Gmail messages...");

    try {

        const response = await fetch(
            `${API_BASE_URL}/gmail/scan?limit=20`,
            {
                credentials: "include"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to scan Gmail."
            );
        }

        scanResults = data.results;

        updateSummary(data.summary);

        renderResults();

        setStatus(
            `Scan completed. ${data.summary.successful} emails analyzed.`
        );

    } catch (error) {

        console.error(error);

        setStatus(
            `Error: ${error.message}`
        );

    } finally {

        scanButton.disabled = false;
    }
}


function connectGmail() {

    window.location.href =
        `${API_BASE_URL}/auth/gmail`;
}


document.querySelectorAll(".filter-btn").forEach(button => {

    button.addEventListener("click", () => {

        document
            .querySelectorAll(".filter-btn")
            .forEach(btn =>
                btn.classList.remove("active")
            );

        button.classList.add("active");

        activeCategory =
            button.dataset.category;

        renderResults();
    });
});


connectGmailButton.addEventListener(
    "click",
    connectGmail
);


scanButton.addEventListener(
    "click",
    scanEmails
);


closeModalButton.addEventListener(
    "click",
    closeEmailDetails
);


emailModal.addEventListener(
    "click",
    (event) => {

        if (event.target === emailModal) {
            closeEmailDetails();
        }

    }
);