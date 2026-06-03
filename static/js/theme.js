const THEME_KEY = "eos-theme";

function applyTheme(theme) {
    const nextTheme = theme === "light" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem(THEME_KEY, nextTheme);

    const label = document.getElementById("theme-toggle-label");
    const toggle = document.getElementById("theme-toggle");
    const icon = document.querySelector(".theme-toggle-icon");
    if (label) {
        label.textContent = nextTheme === "light" ? "Thème sombre" : "Thème clair";
    }
    if (toggle) {
        toggle.setAttribute("aria-pressed", String(nextTheme === "light"));
    }
    if (icon) {
        icon.textContent = nextTheme === "light" ? "☀️" : "🌙";
    }
    
    // Mettre à jour tous les graphiques existants
    updateAllCharts();
    
    window.dispatchEvent(new CustomEvent("eos-theme-change", { detail: { theme: nextTheme } }));
}

// Fonction pour mettre à jour tous les types de graphiques
function updateAllCharts() {
    // Mettre à jour les graphiques EOS Explorer
    if (typeof updateEosChartTheme === 'function') {
        updateEosChartTheme();
    }
    
    // Mettre à jour les graphiques isothermes
    if (typeof updateAllIsothermCharts === 'function') {
        updateAllIsothermCharts();
    }
    
    // Mettre à jour les graphiques Z
    if (typeof updateZChartTheme === 'function') {
        updateZChartTheme();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem(THEME_KEY) || "dark";
    applyTheme(savedTheme);

    const toggle = document.getElementById("theme-toggle");
    if (!toggle) return;

    toggle.addEventListener("click", () => {
        const currentTheme = document.documentElement.dataset.theme || "dark";
        applyTheme(currentTheme === "light" ? "dark" : "light");
    });
});