// ─────────────────────────────────────────
// i18n.js — gestion des langues
// ─────────────────────────────────────────

const SUPPORTED_LANGS = ["en", "fr"];
const DEFAULT_LANG = "en";

let translations = {};
let currentLang = localStorage.getItem("lang") || DEFAULT_LANG;

/**
 * Charge le fichier de traductions pour la langue donnée.
 */
export async function loadTranslations(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) lang = DEFAULT_LANG;
    currentLang = lang;
    localStorage.setItem("lang", lang);

    const res = await fetch(`/static/locales/${lang}.json`);
    translations = await res.json();

    applyTranslations();
    updateFlagButton();
}

/**
 * Retourne la traduction d'une clé (ex: "ui.start", "values.Carnivore")
 * Supporte la notation pointée pour accéder aux sous-clés.
 */
export function t(path, fallback = path) {
    const keys = path.split(".");
    let result = translations;
    for (const key of keys) {
        result = result?.[key];
        if (result === undefined) return fallback;
    }
    return result ?? fallback;
}

/**
 * Traduit une valeur animale (diet, habitat, etc.)
 */
export function tValue(value) {
    return translations?.values?.[value] ?? value;
}

/**
 * Traduit un nom d'animal.
 */
export function tAnimal(name) {
    return translations?.animals?.[name] ?? name;
}

/**
 * Retourne la langue courante.
 */
export function getLang() {
    return currentLang;
}

/**
 * Applique les traductions aux éléments HTML avec data-i18n.
 * Ex: <button data-i18n="ui.start">Start</button>
 */
function applyTranslations() {
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        el.innerText = t(key);
    });
}

/**
 * Met à jour le bouton drapeau selon la langue active.
 */
function updateFlagButton() {
    const btn = document.getElementById("lang-btn");
    if (!btn) return;
    btn.innerText = currentLang === "fr" ? "🇬🇧" : "🇫🇷";
    btn.title = currentLang === "fr" ? "Switch to English" : "Passer en français";
}

/**
 * Bascule entre français et anglais.
 */
export async function toggleLang() {
    const newLang = currentLang === "en" ? "fr" : "en";
    await loadTranslations(newLang);
}

/**
 * Initialise i18n au chargement de la page.
 */
export async function initI18n() {
    await loadTranslations(currentLang);
}