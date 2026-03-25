import * as api from "./api.js";
import * as ui from "./ui.js";

let state = {
    score: 0,
    streak: 0,
    lives: 3,
    username: null,
    timer: null
};

export async function startGame() {
    const username = prompt("Enter your name:");
    if (!username) return;

    state = { score: 0, streak: 0, lives: 3, username, timer: null };

    await api.startGameAPI(username);

    ui.showScreen("game");
    ui.updateScore(0);
    ui.updateStreak(0);
    ui.updateLives(3);
    ui.showResult("");              // 🔥 reset message
    ui.resetCard();                // 🔥 reset animation
    ui.setButtons(false);          // 🔥 sécurité

    loadQuestion();
}

export async function loadQuestion() {
    clearTimeout(state.timer);

    ui.setButtons(false);          // 🔥 désactive pendant chargement

    const data = await api.getQuestionAPI();
    if (data.error) return;

    ui.showQuestion(data);
    ui.resetCard();                // 🔥 reset visuel carte
    ui.showResult("");             // 🔥 clear message

    ui.setButtons(true);           // 🔥 active boutons

    // 🔥 TIMER ANIMÉ (clé du bug)
    state.timer = ui.startTimer(7000, () => answer(null));
}

export async function answer(choice) {
    clearTimeout(state.timer);

    if (state.lives <= 0) return;

    ui.setButtons(false);          // 🔥 empêche spam

    const data = await api.answerAPI(choice);
    if (data.error) return;

    // 🔥 ANIMATION carte
    ui.flashCard(data.correct);

    state.score = data.score;
    state.streak = data.streak;
    state.lives = data.lives;

    ui.updateScore(state.score);
    ui.updateStreak(state.streak);
    ui.updateLives(state.lives);

    // 🔥 message utilisateur
    if (data.correct) {
        ui.showResult("✅ Correct!");
    } else {
        if (state.lives <= 0) {
            gameOver();
            return;
        }

        ui.showResult(
            choice === null
                ? `⏱️ Time's up! Real: ${data.real}`
                : `❌ Wrong! Real: ${data.real}`
        );
    }

    setTimeout(loadQuestion, 1500);
}

export async function gameOver() {
    clearTimeout(state.timer);

    ui.setButtons(false);          // 🔥 stop interaction
    ui.showGameOver(state.score);
    ui.showScreen("game-over");

    await api.submitScoreAPI();
}

export async function restartGame() {
    await startGame();
}