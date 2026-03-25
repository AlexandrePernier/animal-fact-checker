import * as game from "./game.js";
import * as api from "./api.js";
import * as ui from "./ui.js";

window.addEventListener("DOMContentLoaded", () => {

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