const API_URL = "http://localhost:5002";
const SCORE_API_URL = "http://localhost:5004";

document
  .getElementById("complaintForm")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const citizenId = document.getElementById("citizenId").value;
    const description = document.getElementById("description").value;
    const location = document.getElementById("location").value;

    const response = await fetch(API_URL + "/complaints", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        citizen_id: citizenId,
        description: description,
        location: location,
      }),
    });

    const data = await response.json();

    document.getElementById("result").innerHTML = `<h3>Complaint Registered</h3>
             Complaint ID: ${data.complaint_id}<br>
             Status: ${data.status}`;
  });

async function findComplaint() {
  const id = document.getElementById("searchComplaintId").value;
  const response = await fetch(API_URL + "/complaints/" + id);
  const data = await response.json();

  if (response.ok) {
    document.getElementById("complaintDetails").innerHTML =
      `<h3>Complaint Details</h3>
             Complaint ID: ${data.complaint_id}<br>
             Citizen ID: ${data.citizen_id}<br>
             Issue: ${data.description}<br>
             Location: ${data.location}<br>
             Status: ${data.status}`;
  } else {
    document.getElementById("complaintDetails").innerHTML = data.error;
  }
}

document
  .getElementById("scoreButton")
  .addEventListener("click", showCivicScore);
document
  .getElementById("leaderboardButton")
  .addEventListener("click", showLeaderboard);

async function showCivicScore() {
  const citizenId = document.getElementById("citizenId").value;
  const scoreDetails = document.getElementById("scoreDetails");

  if (!citizenId) {
    scoreDetails.textContent = "Enter a Citizen ID first.";
    return;
  }

  const response = await fetch(`${SCORE_API_URL}/score/${citizenId}`);
  const data = await response.json();

  scoreDetails.innerHTML = response.ok
    ? `<h3>Civic Score</h3>
           Citizen ID: ${data.citizen_id}<br>
           Total Score: ${data.total_score}<br>
           Complaints Filed: ${data.complaints_filed}`
    : data.error;
}

async function showLeaderboard() {
  const leaderboardDetails = document.getElementById("leaderboardDetails");
  const response = await fetch(`${SCORE_API_URL}/leaderboard`);
  const data = await response.json();

  if (!response.ok) {
    leaderboardDetails.textContent =
      data.error || "Unable to load leaderboard.";
    return;
  }

  leaderboardDetails.innerHTML = `<h3>Leaderboard</h3>${
    data.length
      ? `<ol>${data.map((entry) => `<li>Citizen ${entry.citizen_id}: ${entry.total_score} points (${entry.complaints_filed} complaints)</li>`).join("")}</ol>`
      : "No scores yet."
  }`;
}
