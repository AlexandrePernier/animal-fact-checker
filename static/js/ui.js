import { t, tAnimal } from "./i18n.js";

export function showScreen(id) {
    ["start-screen", "username-screen", "game", "game-over", "leaderboard-screen"]
        .forEach(el => {
            const element = document.getElementById(el);
            element.classList.add("hidden");
            element.classList.remove("active");
        });

    const target = document.getElementById(id);
    target.classList.remove("hidden");

    if (id === "game-over") {
        target.classList.add("active");
    }
}

export function updateScore(score) {
    document.getElementById("score").innerText = `${t("ui.score")}: ${score}`;
}

export function updateStreak(streak) {
    const el = document.getElementById("streak");
    el.innerText = `${t("ui.streak")}: ${streak}`;
    el.classList.toggle("streak-active", streak >= 3);
}

export function updateLives(lives) {
    document.getElementById("lives").innerText = "❤️".repeat(Math.max(0, lives));
}

export function showQuestion(data) {
    document.getElementById("question").innerText = data.question;

    const img = document.getElementById("animal-img");
    if (data.image) {
        img.src = data.image;
        img.style.display = "block";
    } else {
        img.style.display = "none";
    }
}

export function showResult(text) {
    document.getElementById("result").innerText = text;
}

export function showGameOver(score) {
    document.getElementById("final-score").innerText = `${t("ui.final_score")}: ${score}`;
}

export function renderLeaderboard(data) {
    const container = document.getElementById("leaderboard-list");
    container.innerHTML = "";

    data.top10.forEach((entry, index) => {
        const medal = ["🥇", "🥈", "🥉"][index] || `#${index + 1}`;
        container.innerHTML += `
        <div class="leaderboard-item">
            <div>${medal}</div>
            <div>${entry.username}</div>
            <div>${entry.score}</div>
        </div>`;
    });
}

export function startTimer(duration, onEnd) {
    const bar = document.getElementById("timer-bar");

    bar.style.transition = "none";
    bar.style.width = "100%";

    setTimeout(() => {
        bar.style.transition = `width ${duration}ms linear`;
        bar.style.width = "0%";
    }, 50);

    return setTimeout(onEnd, duration);
}

export function flashCard(isCorrect) {
    const card = document.getElementById("card");
    card.classList.remove("correct", "wrong");
    if (isCorrect) {
        card.classList.add("correct");
    } else {
        card.classList.add("wrong");
    }
}

export function resetCard() {
    const card = document.getElementById("card");
    card.className = "card";
}

export function setButtons(enabled) {
    document.getElementById("trueBtn").disabled = !enabled;
    document.getElementById("falseBtn").disabled = !enabled;
}

/**
 * Rafraîchit les labels de score/streak après un changement de langue.
 */
export function refreshScoreLabels() {
    const scoreEl = document.getElementById("score");
    const streakEl = document.getElementById("streak");
    if (scoreEl) {
        const val = scoreEl.innerText.split(": ")[1] ?? "0";
        scoreEl.innerText = `${t("ui.score")}: ${val}`;
    }
    if (streakEl) {
        const val = streakEl.innerText.split(": ")[1] ?? "0";
        streakEl.innerText = `${t("ui.streak")}: ${val}`;
    }
}