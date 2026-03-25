export async function startGameAPI(username) {
    return fetch("/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username })
    });
}

export async function getQuestionAPI() {
    const res = await fetch("/question");
    return res.json();
}

export async function answerAPI(answer) {
    const res = await fetch("/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
    });
    return res.json();
}

export async function submitScoreAPI() {
    return fetch("/submit_score", { method: "POST" });
}

export async function getLeaderboardAPI() {
    const res = await fetch("/leaderboard");
    return res.json();
}