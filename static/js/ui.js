export function showScreen(id) {
    ["start-screen", "game", "game-over", "leaderboard-screen"]
        .forEach(el => {
            const element = document.getElementById(el);
            element.classList.add("hidden");
            element.classList.remove("active"); // 🔥 reset animation
        });

    const target = document.getElementById(id);
    target.classList.remove("hidden");

    if (id === "game-over") {
        target.classList.add("active");
    }
}

export function updateScore(score) {
    document.getElementById("score").innerText = "Score: " + score;
}

export function updateStreak(streak) {
    const el = document.getElementById("streak");
    el.innerText = "🔥 Streak: " + streak;
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
    document.getElementById("final-score").innerText = "Final Score: " + score;
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