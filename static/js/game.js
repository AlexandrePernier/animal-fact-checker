import * as api from "./api.js";
import * as ui from "./ui.js";
import { t, getLang } from "./i18n.js";

let state = {
    score: 0,
    streak: 0,
    lives: 3,
    username: null,
    timer: null
};

export async function startGame() {
    const username = localStorage.getItem("username");
    if (!username) return;

    state = { score: 0, streak: 0, lives: 3, username, timer: null };
    await api.startGameAPI(username);

    ui.showScreen("game");
    ui.updateScore(0);
    ui.updateStreak(0);
    ui.updateLives(3);
    ui.showResult("");
    ui.resetCard();
    ui.setButtons(false);

    loadQuestion();
}

export async function loadQuestion() {
    clearTimeout(state.timer);
    ui.setButtons(false);

    const data = await api.getQuestionAPI(getLang());
    if (data.error) return;

    ui.showQuestion(data);
    ui.resetCard();
    ui.showResult("");
    ui.setButtons(true);

    state.timer = ui.startTimer(7000, () => answer(null));
}

export async function answer(choice) {
    clearTimeout(state.timer);
    if (state.lives <= 0) return;

    ui.setButtons(false);

    const data = await api.answerAPI(choice);
    if (data.error) return;

    ui.flashCard(data.correct);

    state.score = data.score;
    state.streak = data.streak;
    state.lives = data.lives;

    ui.updateScore(state.score);
    ui.updateStreak(state.streak);
    ui.updateLives(state.lives);

    if (data.correct) {
        // ✅ Amélioration 2 — affiche toujours la vraie valeur
        ui.showResult(`${t("ui.correct_answer")}: ${data.real}`);
    } else {
        if (state.lives <= 0) {
            gameOver();
            return;
        }
        const prefix = choice === null ? t("ui.timeout") : t("ui.wrong");
        ui.showResult(`${prefix}: ${data.real}`);
    }

    setTimeout(loadQuestion, 1500);
}

export async function gameOver() {
    clearTimeout(state.timer);
    ui.setButtons(false);
    ui.showGameOver(state.score);
    ui.showScreen("game-over");
    await api.submitScoreAPI();
}

export async function restartGame() {
    await startGame();
}