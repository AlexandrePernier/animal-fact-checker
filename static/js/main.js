import * as game from "./game.js";
import * as api from "./api.js";
import * as ui from "./ui.js";
import { initI18n, toggleLang } from "./i18n.js";

window.addEventListener("DOMContentLoaded", async () => {

    // Initialise la langue au chargement
    await initI18n();

    document.getElementById("lang-btn").onclick = async () => {
        await toggleLang();
        // Si une partie est en cours, les scores/vies se réaffichent traduits
        ui.refreshScoreLabels();
    };

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
        ui.showScreen("start-screen");
    };

});