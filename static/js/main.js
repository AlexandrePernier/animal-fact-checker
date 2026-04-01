import * as game from "./game.js";
import * as api from "./api.js";
import * as ui from "./ui.js";
import { initI18n, toggleLang, t } from "./i18n.js";

window.addEventListener("DOMContentLoaded", async () => {
    await initI18n();

    // ── Langue ──────────────────────────────────
    document.getElementById("lang-btn").onclick = async () => {
        await toggleLang();
        ui.refreshScoreLabels();
        updateWelcomeMsg();
    };

    // ── Pseudo ──────────────────────────────────
    const savedUsername = localStorage.getItem("username");

    if (savedUsername) {
        showStartScreen(savedUsername);
    } else {
        ui.showScreen("username-screen");
    }

    // Confirmation du pseudo
    document.getElementById("username-confirm-btn").onclick = confirmUsername;
    document.getElementById("username-input").addEventListener("keydown", e => {
        if (e.key === "Enter") confirmUsername();
    });

    // Changer de pseudo
    document.getElementById("change-username-btn").onclick = () => {
        localStorage.removeItem("username");
        document.getElementById("username-input").value = "";
        ui.showScreen("username-screen");
    };

    // ── Jeu ─────────────────────────────────────
    document.getElementById("start-btn").onclick = game.startGame;
    document.getElementById("trueBtn").onclick = () => game.answer(true);
    document.getElementById("falseBtn").onclick = () => game.answer(false);
    document.getElementById("restart-btn").onclick = game.restartGame;

    document.getElementById("leaderboard-btn").onclick = async () => {
        const data = await api.getLeaderboardAPI();
        ui.renderLeaderboard(data);
        ui.showScreen("leaderboard-screen");
    };

    document.getElementById("view-leaderboard-btn").onclick =
        document.getElementById("leaderboard-btn").onclick;

    document.getElementById("back-btn").onclick = () => {
        const username = localStorage.getItem("username");
        showStartScreen(username);
    };
});

function confirmUsername() {
    const input = document.getElementById("username-input").value.trim();
    if (!input) return;
    localStorage.setItem("username", input);
    showStartScreen(input);
}

function showStartScreen(username) {
    ui.showScreen("start-screen");
    updateWelcomeMsg(username);
}

function updateWelcomeMsg(username) {
    const name = username || localStorage.getItem("username");
    if (!name) return;
    const el = document.getElementById("welcome-msg");
    if (el) el.innerText = `${t("ui.welcome")}, ${name} 👋`;
}