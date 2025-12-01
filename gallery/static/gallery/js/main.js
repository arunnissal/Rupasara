// === Theme toggle ===
const THEME_KEY = "rupasara_theme";

function applyTheme(theme) {
    const body = document.body;
    if (theme === "light") {
        body.classList.add("light-theme");
    } else {
        body.classList.remove("light-theme");
        theme = "dark";
    }
    try {
        localStorage.setItem(THEME_KEY, theme);
    } catch (e) {
        // ignore
    }

    const btn = document.getElementById("theme-toggle");
    if (btn) {
        btn.textContent = theme === "light" ? "☀️" : "🌙";
    }
}

function initTheme() {
    let theme = "dark";
    try {
        const saved = localStorage.getItem(THEME_KEY);
        if (saved === "light" || saved === "dark") {
            theme = saved;
        }
    } catch (e) {
        // ignore
    }
    applyTheme(theme);

    const btn = document.getElementById("theme-toggle");
    if (btn) {
        btn.addEventListener("click", () => {
            const nextTheme = document.body.classList.contains("light-theme") ? "dark" : "light";
            applyTheme(nextTheme);
        });
    }
}

// === Search History helpers (localStorage) ===
const HISTORY_KEY = "rupasara_recent_searches";
const MAX_HISTORY = 8;

function loadSearchHistory() {
    try {
        const raw = localStorage.getItem(HISTORY_KEY);
        if (!raw) return [];
        const arr = JSON.parse(raw);
        return Array.isArray(arr) ? arr : [];
    } catch (e) {
        return [];
    }
}

function saveSearchHistory(list) {
    try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(list));
    } catch (e) {
        // ignore
    }
}

function addSearchToHistory(term) {
    term = (term || "").trim();
    if (!term) return;

    let history = loadSearchHistory();

    // remove duplicates (case-insensitive)
    history = history.filter(item => item.toLowerCase() !== term.toLowerCase());
    // add to front
    history.unshift(term);

    // limit list size
    if (history.length > MAX_HISTORY) {
        history = history.slice(0, MAX_HISTORY);
    }

    saveSearchHistory(history);
}

// NEW: clear history helper
function clearSearchHistory() {
    try {
        localStorage.removeItem(HISTORY_KEY);
    } catch (e) {
        // ignore
    }
    // Re-render both containers if they exist
    renderSearchHistory("recent-searches-home", "");
    renderSearchHistory("recent-searches-results", "");
}

// Render history into given container
function renderSearchHistory(containerId, currentQuery) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const history = loadSearchHistory();
    container.innerHTML = "";

    if (!history.length) {
        container.style.display = "none";
        return;
    }

    container.style.display = "block";

    const headerRow = document.createElement("div");
    headerRow.className = "recent-header-row";

    const title = document.createElement("p");
    title.className = "recent-title";
    title.textContent = "Recent searches:";
    headerRow.appendChild(title);

    // Clear link
    const clearLink = document.createElement("button");
    clearLink.type = "button";
    clearLink.className = "link-clear";
    clearLink.textContent = "Clear";
    clearLink.addEventListener("click", clearSearchHistory);
    headerRow.appendChild(clearLink);

    container.appendChild(headerRow);

    const wrap = document.createElement("div");
    wrap.className = "chip-row";

    history.forEach(term => {
        const a = document.createElement("a");
        a.className = "chip-small";
        a.textContent = term;
        a.href = `/search/?q=${encodeURIComponent(term)}`;

        if (currentQuery && term.toLowerCase() === currentQuery.toLowerCase()) {
            a.classList.add("chip-active");
        }

        wrap.appendChild(a);
    });

    container.appendChild(wrap);
}

// === Favorite system (image cards) ===
function initFavoriteButtons() {
    const favButtons = document.querySelectorAll(".fav-btn");
    if (!favButtons.length) return;

    let saved;
    try {
        saved = JSON.parse(localStorage.getItem("rupasara_favorites") || "[]");
        if (!Array.isArray(saved)) saved = [];
    } catch (e) {
        saved = [];
    }

    favButtons.forEach(btn => {
        const thumb = btn.dataset.thumb;
        const full = btn.dataset.full;

        // Mark already saved
        if (saved.some(i => i.full === full)) {
            btn.textContent = "❤️";
        }

        btn.addEventListener("click", () => {
            let favs;
            try {
                favs = JSON.parse(localStorage.getItem("rupasara_favorites") || "[]");
                if (!Array.isArray(favs)) favs = [];
            } catch (e) {
                favs = [];
            }

            const exists = favs.some(i => i.full === full);

            if (exists) {
                favs = favs.filter(i => i.full !== full);
                btn.textContent = "🤍";
            } else {
                favs.push({ thumb, full });
                btn.textContent = "❤️";
            }

            localStorage.setItem("rupasara_favorites", JSON.stringify(favs));
        });
    });
}

// === Page-specific logic ===
document.addEventListener("DOMContentLoaded", function () {
    // ✅ for entry animations
    document.body.classList.add("page-ready");

    // Theme
    initTheme();

    // Home page: only show history if container exists
    const homeContainer = document.getElementById("recent-searches-home");
    if (homeContainer) {
        renderSearchHistory("recent-searches-home", "");
    }

    // Results page: save query + render history
    const resultsContainer = document.getElementById("recent-searches-results");
    if (resultsContainer) {
        const currentQuery = (resultsContainer.dataset.query || "").trim();
        if (currentQuery) {
            addSearchToHistory(currentQuery);
        }
        renderSearchHistory("recent-searches-results", currentQuery || "");
    }

    // Favorites buttons on search results
    initFavoriteButtons();
});
