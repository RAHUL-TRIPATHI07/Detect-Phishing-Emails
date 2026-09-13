const API_BASE_URL = "https://detect-phishing-emails-3.onrender.com";

// =========================================================
// DOM ELEMENTS
// =========================================================

const connectGmailButton = document.getElementById("connect-gmail-btn");
const scanButton = document.getElementById("scan-btn");
const statusElement = document.getElementById("status");
const resultsBody = document.getElementById("results-body");

const emailModal = document.getElementById("email-modal");
const emailDetails = document.getElementById("email-details");
const closeModalButton = document.getElementById("close-modal-btn");
const loadMoreButton = document.getElementById("load-more-btn");

// =========================================================
// APPLICATION STATE
// =========================================================

let scanResults = [];
let activeCategory = "ALL";
let nextPageToken = null;
let isLoadingMore = false;
let isScanning = false;

// =========================================================
// STATUS
// =========================================================

function setStatus(message) {
    if (statusElement) {
        statusElement.textContent = message;
    }
}

// =========================================================
// SCORE FORMATTING
// =========================================================

function formatScore(score) {
    if (typeof score !== "number") {
        return "-";
    }

    return score.toFixed(3);
}

// =========================================================
// CATEGORY STYLING
// =========================================================

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

// =========================================================
// RISK STYLING
// =========================================================

function getRiskClass(risk) {
    if (!risk) {
        return "";
    }

    return `risk-${risk.toLowerCase()}`;
}

// =========================================================
// SUMMARY CALCULATION
// =========================================================

function calculateSummary(results) {
    return {
        total: results.length,

        successful: results.filter(
            email => email.status === "success"
        ).length,

        errors: results.filter(
            email => email.status === "error"
        ).length,

        spam: results.filter(
            email => email.category === "SPAM"
        ).length,

        maybe_spam: results.filter(
            email => email.category === "MAYBE SPAM"
        ).length,

        phishing: results.filter(
            email => email.category === "PHISHING"
        ).length,

        both: results.filter(
            email => email.category === "BOTH"
        ).length,

        none: results.filter(
            email => email.category === "NONE"
        ).length
    };
}

// =========================================================
// UPDATE DASHBOARD SUMMARY
// =========================================================

function updateSummary(summary) {
    if (!summary) {
        return;
    }

    const totalCount = document.getElementById("total-count");
    const spamCount = document.getElementById("spam-count");
    const maybeSpamCount = document.getElementById("maybe-spam-count");
    const phishingCount = document.getElementById("phishing-count");
    const bothCount = document.getElementById("both-count");
    const noneCount = document.getElementById("none-count");

    if (totalCount) {
        totalCount.textContent = summary.total ?? 0;
    }

    if (spamCount) {
        spamCount.textContent = summary.spam ?? 0;
    }

    if (maybeSpamCount) {
        maybeSpamCount.textContent = summary.maybe_spam ?? 0;
    }

    if (phishingCount) {
        phishingCount.textContent = summary.phishing ?? 0;
    }

    if (bothCount) {
        bothCount.textContent = summary.both ?? 0;
    }

    if (noneCount) {
        noneCount.textContent = summary.none ?? 0;
    }
}

// =========================================================
// RENDER RESULTS
// =========================================================

function renderResults(results = scanResults) {

    if (!resultsBody) {
        return;
    }

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

        // -------------------------------------------------
        // ERROR RESULT
        // -------------------------------------------------

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

        // -------------------------------------------------
        // NORMAL RESULT
        // -------------------------------------------------

        row.innerHTML = `
            <td class="email-subject">
                ${escapeHtml(email.subject || "(No subject)")}
            </td>

            <td>
                ${escapeHtml(email.sender || "-")}
            </td>

            <td>
                <span class="badge ${getCategoryClass(email.category)}">
                    ${escapeHtml(email.category || "NONE")}
                </span>
            </td>

            <td class="score">
                ${formatScore(email.spam_score)}
            </td>

            <td class="score">
                ${formatScore(email.phishing_score)}
            </td>

            <td class="${getRiskClass(email.risk_level)}">
                ${escapeHtml(email.risk_level || "-")}
            </td>
        `;

        row.addEventListener(
            "click",
            () => showEmailDetails(email)
        );

        resultsBody.appendChild(row);
    });
}

// =========================================================
// EMAIL DETAILS MODAL
// =========================================================

function showEmailDetails(email) {

    if (!emailDetails || !emailModal) {
        return;
    }

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
                ${escapeHtml(email.category || "NONE")}
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

// =========================================================
// CLOSE MODAL
// =========================================================

function closeEmailDetails() {

    if (!emailModal) {
        return;
    }

    emailModal.classList.add("hidden");
}

// =========================================================
// HTML ESCAPING
// =========================================================

function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    const div = document.createElement("div");

    div.textContent = String(value);

    return div.innerHTML;
}

// =========================================================
// API RESPONSE PARSER
// =========================================================

async function parseApiResponse(response) {

    const contentType =
        response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        return await response.json();
    }

    const text = await response.text();

    return {
        detail: text || "Unexpected server response."
    };
}

// =========================================================
// INITIAL GMAIL SCAN
// =========================================================

async function scanEmails() {

    if (isScanning) {
        return;
    }

    isScanning = true;

    scanButton.disabled = true;

    // Reset previous scan state.
    scanResults = [];
    nextPageToken = null;

    updateLoadMoreButton();

    setStatus("Scanning Gmail messages...");

    try {

        const response = await fetch(
            `${API_BASE_URL}/gmail/scan?limit=20`,
            {
                method: "GET",
                credentials: "include"
            }
        );

        const data = await parseApiResponse(response);

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to scan Gmail."
            );
        }

        // Store first page.
        scanResults = Array.isArray(data.results)
            ? data.results
            : [];

        // Store pagination token.
        nextPageToken =
            data.next_page_token || null;

        // Use backend summary when available.
        // Otherwise calculate it locally.
        const summary =
            data.summary || calculateSummary(scanResults);

        updateSummary(summary);

        renderResults();

        const successful =
            summary.successful ??
            scanResults.filter(
                email => email.status === "success"
            ).length;

        setStatus(
            `Scan completed. ${successful} emails analyzed.`
        );

        updateLoadMoreButton();

    } catch (error) {

        console.error("Gmail scan failed:", error);

        setStatus(
            `Error: ${error.message || "Failed to scan Gmail."}`
        );

        // Prevent stale pagination after a failed scan.
        nextPageToken = null;

        updateLoadMoreButton();

    } finally {

        isScanning = false;

        scanButton.disabled = false;

        updateLoadMoreButton();
    }
}

// =========================================================
// LOAD MORE EMAILS
// =========================================================

async function loadMoreEmails() {

    if (!nextPageToken || isLoadingMore || isScanning) {
        return;
    }

    isLoadingMore = true;

    updateLoadMoreButton();

    setStatus("Loading more Gmail messages...");

    try {

        const response = await fetch(
            `${API_BASE_URL}/gmail/scan?limit=20&page_token=${encodeURIComponent(nextPageToken)}`,
            {
                method: "GET",
                credentials: "include"
            }
        );

        const data = await parseApiResponse(response);

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to load more emails."
            );
        }

        const newResults = Array.isArray(data.results)
            ? data.results
            : [];

        // Append the new page.
        scanResults = [
            ...scanResults,
            ...newResults
        ];

        // Store next pagination token.
        nextPageToken =
            data.next_page_token || null;

        // Recalculate complete summary.
        const summary =
            calculateSummary(scanResults);

        updateSummary(summary);

        renderResults();

        setStatus(
            `Loaded ${newResults.length} more emails. ` +
            `${summary.successful} emails analyzed in total.`
        );

        updateLoadMoreButton();

    } catch (error) {

        console.error(
            "Loading more emails failed:",
            error
        );

        setStatus(
            `Error: ${error.message || "Failed to load more emails."}`
        );

    } finally {

        isLoadingMore = false;

        updateLoadMoreButton();
    }
}

// =========================================================
// CONNECT GMAIL
// =========================================================

function connectGmail() {

    window.location.href =
        `${API_BASE_URL}/auth/gmail`;
}

// =========================================================
// FILTERS
// =========================================================

document
    .querySelectorAll(".filter-btn")
    .forEach(button => {

        button.addEventListener("click", () => {

            document
                .querySelectorAll(".filter-btn")
                .forEach(btn =>
                    btn.classList.remove("active")
                );

            button.classList.add("active");

            activeCategory =
                button.dataset.category || "ALL";

            renderResults();
        });
    });

// =========================================================
// EVENT LISTENERS
// =========================================================

if (connectGmailButton) {
    connectGmailButton.addEventListener(
        "click",
        connectGmail
    );
}

if (scanButton) {
    scanButton.addEventListener(
        "click",
        scanEmails
    );
}

if (closeModalButton) {
    closeModalButton.addEventListener(
        "click",
        closeEmailDetails
    );
}

if (emailModal) {
    emailModal.addEventListener(
        "click",
        (event) => {

            if (event.target === emailModal) {
                closeEmailDetails();
            }

        }
    );
}

// =========================================================
// SIDEBAR NAVIGATION
// =========================================================

const navOverview =
    document.getElementById("nav-overview");

const navMailbox =
    document.getElementById("nav-mailbox");

const navThreats =
    document.getElementById("nav-threats");

const navIntelligence =
    document.getElementById("nav-intelligence");

const navigationItems = [
    navOverview,
    navMailbox,
    navThreats,
    navIntelligence
].filter(Boolean);

// =========================================================
// ACTIVE NAVIGATION
// =========================================================

function setActiveNavigation(activeItem) {

    navigationItems.forEach(item => {
        item.classList.remove("active");
    });

    if (activeItem) {
        activeItem.classList.add("active");
    }
}

// =========================================================
// SCROLL TO SECTION
// =========================================================

function scrollToSection(sectionId) {

    const section =
        document.getElementById(sectionId);

    if (!section) {
        return;
    }

    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

// =========================================================
// NAVIGATION EVENTS
// =========================================================

if (navOverview) {

    navOverview.addEventListener("click", () => {

        setActiveNavigation(navOverview);

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    });
}

if (navMailbox) {

    navMailbox.addEventListener("click", () => {

        setActiveNavigation(navMailbox);

        scrollToSection("mailbox-section");
    });
}

if (navThreats) {

    navThreats.addEventListener("click", () => {

        setActiveNavigation(navThreats);

        scrollToSection("threats-section");
    });
}

if (navIntelligence) {

    navIntelligence.addEventListener("click", () => {

        setActiveNavigation(navIntelligence);

        scrollToSection("ai-intelligence-section");
    });
}

// =========================================================
// LOAD MORE BUTTON
// =========================================================

function updateLoadMoreButton() {

    if (!loadMoreButton) {
        return;
    }

    if (nextPageToken) {

        loadMoreButton.classList.remove("hidden");

        loadMoreButton.disabled =
            isLoadingMore || isScanning;

        if (isLoadingMore) {

            loadMoreButton.textContent =
                "Loading...";

        } else {

            loadMoreButton.textContent =
                "Load More Emails";
        }

    } else {

        loadMoreButton.classList.add("hidden");

        loadMoreButton.disabled = false;

        loadMoreButton.textContent =
            "Load More Emails";
    }
}

if (loadMoreButton) {

    loadMoreButton.addEventListener(
        "click",
        loadMoreEmails
    );
}

// =========================================================
// GMAIL CONNECTION STATUS
// =========================================================

async function checkGmailConnection() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/auth/gmail/status`,
            {
                method: "GET",
                credentials: "include"
            }
        );

        const data =
            await parseApiResponse(response);

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Failed to check Gmail connection."
            );
        }

        if (data.connected) {

            // Connected state can be enhanced later.

        } else {

            // Disconnected state can be enhanced later.
        }

    } catch (error) {

        console.error(
            "Failed to check Gmail connection:",
            error
        );
    }
}

// =========================================================
// INITIAL UI STATE
// =========================================================

updateLoadMoreButton();