const SAFE_METHODS = ["GET", "HEAD", "OPTIONS"];

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function humanizeFieldName(name) {
    const words = name.replaceAll("_", " ");
    return words.charAt(0).toUpperCase() + words.slice(1);
}

function apiErrorMessage(data, status) {
    const fallback = `Request failed (HTTP ${status}).`;
    if (!data || typeof data !== "object") return fallback;
    if (typeof data.detail === "string") return data.detail;

    const messages = Object.entries(data).flatMap(([field, errors]) => {
        const prefix = field === "non_field_errors" ? "" : `${humanizeFieldName(field)}: `;
        return [].concat(errors)
            .filter((error) => typeof error === "string")
            .map((error) => prefix + error);
    });
    return messages.join(" ") || fallback;
}

class ApiError extends Error {
    constructor(status, data) {
        super(apiErrorMessage(data, status));
        this.name = "ApiError";
        this.status = status;
        this.data = data;
    }
}

function errorMessageFor(error) {
    if (error instanceof ApiError) return error.message;
    return "Couldn't reach the server. Check your connection and try again.";
}

async function requestJson(url, { method = "GET", body, signal } = {}) {
    const headers = { Accept: "application/json" };
    if (!SAFE_METHODS.includes(method)) headers["X-CSRFToken"] = getCookie("csrftoken") ?? "";
    if (body !== undefined) headers["Content-Type"] = "application/json";

    const response = await fetch(url, {
        method,
        headers,
        signal,
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (response.status === 204) return null;

    const data = await response.json().catch(() => null);
    if (!response.ok) throw new ApiError(response.status, data);
    return data;
}
