const API_URL = "http://localhost:5004";

async function checkScore() {
    const citizenId = document.getElementById("citizenId").value;
    const response = await fetch(API_URL + "/score/" + citizenId);
    const data = await response.json();

    document.getElementById("scoreResult").innerHTML =
        `<h3>Score Summary</h3>
         Citizen ID: ${data.citizen_id}<br>
         Total Score: ${data.total_score}<br>
         Complaints Filed: ${data.complaints_filed}`;
}

async function loadLeaderboard() {
    const response = await fetch(API_URL + "/leaderboard");
    const data = await response.json();

    const resultDiv = document.getElementById("leaderboardResult");

    if (data.length === 0) {
        resultDiv.innerHTML = "<p>No scores yet.</p>";
        return;
    }

    let rows = data.map(entry => `
        <tr>
            <td>#${entry.rank}</td>
            <td>Citizen ${entry.citizen_id}</td>
            <td>${entry.total_score} pts</td>
            <td>${entry.complaints_filed}</td>
        </tr>
    `).join("");

    resultDiv.innerHTML = `
        <table>
            <tr>
                <th>Rank</th>
                <th>Citizen</th>
                <th>Score</th>
                <th>Complaints</th>
            </tr>
            ${rows}
        </table>
    `;
}
