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

async function sendJson(url, method, payload) {
    const response = await fetch(url, {
        method,
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken") ?? "",
        },
        body: payload === undefined ? undefined : JSON.stringify(payload),
    });
    if (response.status === 204) return null;

    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(apiErrorMessage(data, response.status));
    return data;
}
