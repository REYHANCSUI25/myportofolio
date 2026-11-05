const pageConfig = JSON.parse(document.getElementById("education-page-config").textContent);
const SEARCH_DEBOUNCE_DELAY = 300;
const FORM_FIELDS = ["institution", "degree", "description", "started_at", "ended_at"];
const DATE_FIELDS = new Set(["started_at", "ended_at"]);

const loadingState = document.getElementById("loading");
const errorState = document.getElementById("error");
const emptyState = document.getElementById("empty");
const gridContainer = document.getElementById("grid");
const searchForm = document.getElementById("education-search-form");
const searchInput = document.getElementById("search-input");
const addButton = document.querySelector(".education-add-button");
const educationModal = document.getElementById("education-modal");
const educationForm = document.getElementById("education-form");
const modalTitle = document.getElementById("education-modal-title");
const submitButton = document.getElementById("education-form-submit");

let educationsAbortController;
let searchDebounceTimer;
let editingEntry = null;
let modalTrigger = null;

function urlFor(pattern, id) {
    return pattern.replace(pageConfig.placeholderId, encodeURIComponent(id));
}

function yearOf(isoDate) {
    return String(isoDate ?? "").slice(0, 4);
}

function displayPageSection({ showLoading = false, showError = false, showEmpty = false, showGrid = false }) {
    loadingState.classList.toggle("hide", !showLoading);
    errorState.classList.toggle("hide", !showError);
    emptyState.classList.toggle("hide", !showEmpty);
    gridContainer.classList.toggle("hide", !showGrid);
}

function showListOrEmpty() {
    const hasCards = gridContainer.children.length > 0;
    displayPageSection({ showGrid: hasCards, showEmpty: !hasCards });
}

function findCard(id) {
    return gridContainer.querySelector(`.education-card[data-id="${CSS.escape(id)}"]`);
}

function removeCard(id) {
    findCard(id)?.remove();
    showListOrEmpty();
}

function showMissingEntry(id) {
    removeCard(id);
    showToast("Entry no longer exists", "It was deleted elsewhere, so it was removed from this page.", "error");
}

function buildStarControl(education) {
    if (!pageConfig.isAuthenticated) {
        const next = encodeURIComponent(window.location.pathname);
        return `<a href="${escapeHtml(pageConfig.loginUrl)}?next=${next}" class="button-star">☆ Log in to star</a>`;
    }
    const activeClass = education.is_starred ? " button-star--active" : "";
    const label = education.is_starred ? "★ Starred" : "☆ Star";
    return `<button type="button" class="button-star${activeClass}" data-action="star">${label}</button>`;
}

function buildActionControls() {
    const edit = pageConfig.canEdit
        ? `<button type="button" class="button button-secondary" data-action="edit" aria-haspopup="dialog">Edit</button>`
        : "";
    const remove = pageConfig.canDelete
        ? `<button type="button" class="button button-danger" data-action="delete">Delete</button>`
        : "";
    return edit || remove ? `<div class="education-card-actions">${edit}${remove}</div>` : "";
}

function buildEducationCardElement(education) {
    const card = document.createElement("article");
    card.className = "education-card";
    card.dataset.id = education.id;
    card.dataset.label = `${education.degree} at ${education.institution}`;

    const periodEnd = education.is_ongoing ? "Present" : yearOf(education.ended_at);
    const ongoingBadge = education.is_ongoing
        ? `<span class="education-status education-status--ongoing">Ongoing</span>`
        : "";
    const starCount = Number(education.star_count) || 0;

    card.innerHTML = `
        <span class="education-institution">${escapeHtml(education.institution)}</span>
        <h2>${escapeHtml(education.degree)}</h2>
        <p class="education-description">${escapeHtml(education.description)}</p>
        <p class="education-period">${escapeHtml(yearOf(education.started_at))} – ${escapeHtml(periodEnd)}</p>
        ${ongoingBadge}
        <div class="star-row">
            ${buildStarControl(education)}
            <span class="star-count">${starCount} star${starCount === 1 ? "" : "s"}</span>
        </div>
        ${buildActionControls()}
    `;
    return card;
}

async function fetchEducations(searchQuery = "", { quiet = false } = {}) {
    educationsAbortController?.abort();
    educationsAbortController = new AbortController();
    if (!quiet) displayPageSection({ showLoading: true });

    try {
        const url = new URL(pageConfig.listUrl, window.location.origin);
        if (searchQuery) url.searchParams.set("institution", searchQuery);

        const educations = await requestJson(url, { signal: educationsAbortController.signal });
        gridContainer.replaceChildren(...educations.map(buildEducationCardElement));
        showListOrEmpty();
    } catch (error) {
        if (error.name === "AbortError") return;
        console.error("Error loading education entries:", error);
        displayPageSection({ showError: true });
    }
}

function readEducationForm() {
    const fields = new FormData(educationForm);
    return Object.fromEntries(FORM_FIELDS.map((field) => {
        const value = fields.get(field) ?? "";
        return [field, DATE_FIELDS.has(field) && value === "" ? null : value];
    }));
}

function fillEducationForm(education) {
    for (const field of FORM_FIELDS) {
        educationForm.elements[field].value = education[field] ?? "";
    }
}

function changedFields(original, current) {
    return Object.fromEntries(
        Object.entries(current).filter(([field, value]) => value !== original[field]),
    );
}

function errorElementFor(input) {
    return document.getElementById(`${input.id}-error`);
}

function clearFieldError(input) {
    const message = errorElementFor(input);
    if (!message) return;
    message.hidden = true;
    message.textContent = "";
    input.removeAttribute("aria-invalid");
    input.removeAttribute("aria-describedby");
}

function clearFieldErrors() {
    for (const field of FORM_FIELDS) clearFieldError(educationForm.elements[field]);
}

function showFieldErrors(errors) {
    let firstInvalid = null;
    for (const field of FORM_FIELDS) {
        if (!errors?.[field]) continue;
        const input = educationForm.elements[field];
        const message = errorElementFor(input);
        message.textContent = [].concat(errors[field]).join(" ");
        message.hidden = false;
        input.setAttribute("aria-invalid", "true");
        input.setAttribute("aria-describedby", message.id);
        firstInvalid ??= input;
    }
    firstInvalid?.focus();
}

function openEducationModal(trigger, education = null) {
    modalTrigger = trigger;
    educationForm.reset();
    clearFieldErrors();
    if (education) fillEducationForm(education);
    editingEntry = education ? { id: education.id, original: readEducationForm() } : null;
    modalTitle.textContent = education ? "Edit Education" : "Add Education";
    submitButton.textContent = education ? "Save Changes" : "Add Education";
    educationModal.showPopover();
    educationForm.elements.institution.focus();
}

function closeEducationModal() {
    if (educationModal.matches(":popover-open")) educationModal.hidePopover();
}

async function showSavedEducation(saved, changes) {
    const searchQuery = searchInput.value.trim();
    const listChanges = "started_at" in changes || (searchQuery !== "" && "institution" in changes);
    closeEducationModal();

    if (listChanges) {
        await fetchEducations(searchQuery, { quiet: true });
    } else {
        findCard(saved.id)?.replaceWith(buildEducationCardElement(saved));
    }
    findCard(saved.id)?.querySelector('[data-action="edit"]')?.focus();
}

async function submitEducationForm(event) {
    event.preventDefault();
    const entry = editingEntry;
    const values = readEducationForm();
    const changes = entry ? changedFields(entry.original, values) : values;

    if (entry && Object.keys(changes).length === 0) {
        closeEducationModal();
        showToast("No changes", "Nothing was edited, so nothing was saved.");
        return;
    }

    submitButton.disabled = true;
    clearFieldErrors();
    try {
        if (entry) {
            const saved = await requestJson(urlFor(pageConfig.detailUrl, entry.id), {
                method: "PATCH",
                body: changes,
            });
            await showSavedEducation(saved, changes);
            showToast("Success", "Education entry updated.", "success");
        } else {
            await requestJson(pageConfig.listUrl, { method: "POST", body: values });
            closeEducationModal();
            showToast("Success", "New education entry added successfully!", "success");
            await fetchEducations(searchInput.value.trim(), { quiet: true });
        }
    } catch (error) {
        if (entry && error instanceof ApiError && error.status === 404) {
            closeEducationModal();
            showMissingEntry(entry.id);
            return;
        }
        if (error instanceof ApiError && error.status === 400) showFieldErrors(error.data);
        showToast(entry ? "Failed to save changes" : "Failed to add education", errorMessageFor(error), "error");
    } finally {
        submitButton.disabled = false;
    }
}

async function handleCardAction(event) {
    const button = event.target.closest("button[data-action]");
    if (!button || button.disabled) return;

    const card = button.closest(".education-card");
    const { id, label } = card.dataset;
    const action = button.dataset.action;
    if (action === "delete" && !window.confirm(`Delete ${label}?`)) return;

    button.disabled = true;
    try {
        if (action === "star") {
            const updated = buildEducationCardElement(
                await requestJson(urlFor(pageConfig.starUrl, id), { method: "POST" }),
            );
            card.replaceWith(updated);
            updated.querySelector('[data-action="star"]').focus();
        } else if (action === "edit") {
            openEducationModal(button, await requestJson(urlFor(pageConfig.detailUrl, id)));
        } else if (action === "delete") {
            await requestJson(urlFor(pageConfig.detailUrl, id), { method: "DELETE" });
            removeCard(id);
            showToast("Success", "Education entry deleted.", "success");
        }
    } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
            showMissingEntry(id);
        } else {
            showToast("Request failed", errorMessageFor(error), "error");
        }
    } finally {
        button.disabled = false;
    }
}

addButton?.addEventListener("click", () => openEducationModal(addButton));
educationForm?.addEventListener("submit", submitEducationForm);
educationForm?.addEventListener("input", (event) => clearFieldError(event.target));
educationModal?.addEventListener("toggle", (event) => {
    if (event.newState !== "closed") return;
    editingEntry = null;
    if (modalTrigger?.isConnected) modalTrigger.focus();
    modalTrigger = null;
});
gridContainer.addEventListener("click", handleCardAction);

searchInput.addEventListener("input", () => {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(
        () => fetchEducations(searchInput.value.trim()),
        SEARCH_DEBOUNCE_DELAY,
    );
});

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    clearTimeout(searchDebounceTimer);
    fetchEducations(searchInput.value.trim());
});

fetchEducations(searchInput.value.trim());
