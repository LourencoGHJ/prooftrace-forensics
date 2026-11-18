const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function toast(message) {
    const element = $("#toast");
    element.textContent = message;
    element.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => element.classList.remove("show"), 3200);
}

function navigate(view) {
    $$(".view").forEach((item) => item.classList.toggle("active", item.id === `view-${view}`));
    $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === view));
    const labels = { overview: "Overview", analysis: "PDF Analysis", comparison: "Comparison Lab" };
    $("#breadcrumb-current").textContent = labels[view] || "Overview";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

$$("[data-view]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.view)));
$$("[data-go]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.go)));

function validPdf(file) {
    if (!file) return false;
    if (file.size > 50 * 1024 * 1024) {
        toast("File exceeds the 50 MB limit.");
        return false;
    }
    if (!file.name.toLowerCase().endsWith(".pdf")) {
        toast("Please select a PDF file.");
        return false;
    }
    return true;
}

const analysisInput = $("#analysis-file");
const inspectButton = $("#inspect-button");

analysisInput.addEventListener("change", () => {
    const file = analysisInput.files[0];
    if (file && validPdf(file)) {
        $("#analysis-filename").textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`;
        inspectButton.disabled = false;
    } else {
        inspectButton.disabled = true;
    }
});

const dropZone = $("#analysis-drop");
["dragenter", "dragover"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragover");
}));
["dragleave", "drop"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragover");
}));
dropZone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];
    if (!file || !validPdf(file)) return;
    const transfer = new DataTransfer();
    transfer.items.add(file);
    analysisInput.files = transfer.files;
    analysisInput.dispatchEvent(new Event("change"));
});

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
}

function tableRows(object) {
    return Object.entries(object || {}).map(([key, value]) => `
        <tr><th>${escapeHtml(key)}</th><td>${escapeHtml(
            typeof value === "object" ? JSON.stringify(value) : value
        )}</td></tr>`).join("");
}

function renderInspection(data) {
    const metadata = data.metadata || {};
    const signatures = data.signature_fields || [];
    const pages = data.text_pages || [];
    const revisions = data.revision_markers || [];

    $("#analysis-results").innerHTML = `
        <div class="result-card">
            <h3>Inspection summary</h3>
            <div class="metric-grid">
                <div class="metric"><span>Pages</span><strong>${escapeHtml(data.page_count)}</strong></div>
                <div class="metric"><span>File size</span><strong>${(data.size_bytes / 1024).toFixed(1)} KB</strong></div>
                <div class="metric"><span>PDF version</span><strong>${escapeHtml(data.pdf_version)}</strong></div>
            </div>
        </div>
        <div class="result-card">
            <h3>Cryptographic fingerprint</h3>
            <table class="data-table">
                <tr><th>SHA-256</th><td class="hash-value">${escapeHtml(data.sha256)}</td></tr>
            </table>
        </div>
        <div class="result-card">
            <h3>Document properties</h3>
            <table class="data-table">
                <tr><th>Filename</th><td>${escapeHtml(data.file)}</td></tr>
                ${tableRows(metadata)}
                <tr><th>Signature fields</th><td>${signatures.length ? signatures.map(escapeHtml).join(", ") : "None detected"}</td></tr>
                <tr><th>Signature validation</th><td><span class="tag warning">${escapeHtml(data.signature_validation)}</span></td></tr>
                <tr><th>Revision markers</th><td>${escapeHtml(data.revision_marker_count)}</td></tr>
            </table>
        </div>
        <div class="result-card">
            <h3>Page text extraction</h3>
            ${pages.map((page) => `
                <div style="border-top:1px solid #26334a;padding:12px 0">
                    <strong style="font-size:11px">Page ${escapeHtml(page.page)}</strong>
                    <p class="muted" style="font-size:11px;line-height:1.6;white-space:pre-wrap">${escapeHtml(page.text ?? page.error ?? "No text extracted")}</p>
                </div>`).join("")}
        </div>
        <div class="result-card">
            <h3>Analysis limitations</h3>
            <ul class="muted" style="font-size:11px;line-height:1.9;padding-left:18px">
                ${(data.limitations || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
        </div>`;
}

inspectButton.addEventListener("click", async () => {
    const file = analysisInput.files[0];
    if (!validPdf(file)) return;
    const body = new FormData();
    body.append("file", file);
    inspectButton.disabled = true;
    inspectButton.textContent = "Inspecting…";
    $("#analysis-results").innerHTML = '<div class="empty-state">Inspecting document. Please wait…</div>';

    try {
        const response = await fetch("/api/pdf/inspect", { method: "POST", body });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Inspection failed.");
        renderInspection(data);
        toast("PDF inspection completed.");
        loadDashboard();
    } catch (error) {
        $("#analysis-results").innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    } finally {
        inspectButton.disabled = false;
        inspectButton.innerHTML = 'Inspect document <span>→</span>';
    }
});

const firstInput = $("#first-file");
const secondInput = $("#second-file");
const compareButton = $("#compare-button");

function updateComparisonButton() {
    compareButton.disabled = !(firstInput.files[0] && secondInput.files[0]);
}
firstInput.addEventListener("change", () => {
    const file = firstInput.files[0];
    if (file && validPdf(file)) $("#first-filename").textContent = file.name;
    else firstInput.value = "";
    updateComparisonButton();
});
secondInput.addEventListener("change", () => {
    const file = secondInput.files[0];
    if (file && validPdf(file)) $("#second-filename").textContent = file.name;
    else secondInput.value = "";
    updateComparisonButton();
});

function renderComparison(data) {
    const changes = data.page_text_changes || [];
    const metadata = data.metadata_changes || {};
    $("#comparison-results").innerHTML = `
        <div class="result-card">
            <h3>Comparison summary</h3>
            <div class="metric-grid">
                <div class="metric"><span>Byte-identical</span><strong>${data.same_bytes ? "Yes" : "No"}</strong></div>
                <div class="metric"><span>Page count changed</span><strong>${data.page_count_changed ? "Yes" : "No"}</strong></div>
                <div class="metric"><span>Changed pages</span><strong>${changes.length}</strong></div>
            </div>
        </div>
        <div class="result-card">
            <h3>File fingerprints</h3>
            <table class="data-table">
                <tr><th>Original · ${escapeHtml(data.before.file)}</th><td class="hash-value">${escapeHtml(data.before.sha256)}</td></tr>
                <tr><th>Modified · ${escapeHtml(data.after.file)}</th><td class="hash-value">${escapeHtml(data.after.sha256)}</td></tr>
                <tr><th>Original size</th><td>${escapeHtml(data.before.size_bytes)} bytes</td></tr>
                <tr><th>Modified size</th><td>${escapeHtml(data.after.size_bytes)} bytes</td></tr>
            </table>
        </div>
        <div class="result-card">
            <h3>Page text differences</h3>
            ${changes.length ? changes.map((change) => `
                <div style="border-top:1px solid #26334a;padding:12px 0">
                    <strong style="font-size:11px">Page ${escapeHtml(change.page)}</strong>
                    <div class="comparison-inputs" style="margin-top:10px">
                        <div><span class="muted small">BEFORE</span><p style="font-size:11px;white-space:pre-wrap">${escapeHtml(change.before ?? "No page")}</p></div>
                        <div><span class="muted small">AFTER</span><p style="font-size:11px;white-space:pre-wrap">${escapeHtml(change.after ?? "No page")}</p></div>
                    </div>
                </div>`).join("") : '<p class="muted small">No extracted page-text differences detected.</p>'}
        </div>
        <div class="result-card">
            <h3>Metadata differences</h3>
            ${Object.keys(metadata).length ? `<table class="data-table">
                ${Object.entries(metadata).map(([key, values]) => `
                    <tr><th>${escapeHtml(key)}</th><td><span class="muted">Before:</span> ${escapeHtml(values.before)}<br><span class="muted">After:</span> ${escapeHtml(values.after)}</td></tr>
                `).join("")}
            </table>` : '<p class="muted small">No metadata differences detected.</p>'}
        </div>
        <div class="result-card">
            <h3>Comparison limitations</h3>
            <ul class="muted" style="font-size:11px;line-height:1.9;padding-left:18px">
                ${(data.limitations || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
        </div>`;
}

compareButton.addEventListener("click", async () => {
    const first = firstInput.files[0];
    const second = secondInput.files[0];
    if (!validPdf(first) || !validPdf(second)) return;

    const body = new FormData();
    body.append("first", first);
    body.append("second", second);
    compareButton.disabled = true;
    compareButton.textContent = "Comparing…";
    $("#comparison-results").innerHTML = '<div class="empty-state">Comparing documents. Please wait…</div>';

    try {
        const response = await fetch("/api/pdf/compare", { method: "POST", body });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Comparison failed.");
        renderComparison(data);
        toast("Document comparison completed.");
        loadDashboard();
    } catch (error) {
        $("#comparison-results").innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    } finally {
        compareButton.disabled = false;
        compareButton.innerHTML = 'Compare documents <span>⇄</span>';
    }
});

/* Dashboard data */
function formatActivityTime(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Time unavailable";
    return date.toLocaleString(undefined, {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit"
    });
}

async function loadDashboard() {
    try {
        const response = await fetch("/api/dashboard");
        if (!response.ok) throw new Error("Dashboard data unavailable.");

        const data = await response.json();

        $("#stat-total").textContent = data.total_operations;
        $("#stat-inspections").textContent = data.inspections;
        $("#stat-comparisons").textContent = data.comparisons;
        const isOnline = data.status === "online";
        $("#stat-status").textContent = isOnline ? "Online" : "Offline";
        $("#stat-status").classList.toggle("status-offline", !isOnline);
        $("#stat-storage").textContent = "Session-only activity";
        const systemStatus = $(".system-status");
        systemStatus.classList.toggle("is-offline", !isOnline);
        systemStatus.lastChild.textContent = isOnline ? " SYSTEM ONLINE" : " SERVICE UNAVAILABLE";

        const activity = $("#recent-activity");

        if (!data.recent_activity.length) {
            activity.innerHTML = '<div class="empty-state">No completed operations in this session yet. Your completed PDF inspections and comparisons will appear here.</div>';
            return;
        }

        activity.innerHTML = data.recent_activity.map((item) => {
            const isComparison = item.operation === "PDF comparison";
            return `
                <div class="activity-row">
                    <div class="activity-icon ${isComparison ? "compare" : ""}">${isComparison ? "⇄" : "⌕"}</div>
                    <div class="activity-description">
                        <strong>${escapeHtml(item.operation)}</strong>
                        <small>${escapeHtml(item.filename)}</small>
                    </div>
                    <span class="activity-time">${escapeHtml(formatActivityTime(item.timestamp))}</span>
                </div>`;
        }).join("");
    } catch (error) {
        $("#stat-status").textContent = "Unavailable";
        $("#stat-status").classList.add("status-offline");
        $("#stat-storage").textContent = "Could not reach local API";
        const systemStatus = $(".system-status");
        systemStatus.classList.add("is-offline");
        systemStatus.lastChild.textContent = " SERVICE UNAVAILABLE";
        $("#recent-activity").innerHTML = '<div class="error-state">Could not load dashboard activity. Check that the local server is running.</div>';
    }
}

loadDashboard();
