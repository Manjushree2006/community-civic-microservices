const VOLUNTEER_API = "http://localhost:5005/volunteers";
const SIGNUP_API = "http://localhost:5005/signups";

document.getElementById("volunteerForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    const btn = document.getElementById("registerBtn");
    const name = document.getElementById("name").value;
    const phone = document.getElementById("phone").value;
    const skill = document.getElementById("skill").value;

    setLoading(btn, true, "Joining...");
    try {
        const response = await fetch(VOLUNTEER_API, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name, phone, skill})
        });
        const data = await response.json();

        if (response.ok) {
            document.getElementById("result").innerHTML = `
                <div class="stamp-wrap">
                    <div class="stamp volunteers">WELCOME<br>ABOARD</div>
                    <div class="stamp-detail">
                        <p class="big">Volunteer #${data.volunteer_id}</p>
                        <p>${data.name} — ${data.skill}</p>
                    </div>
                </div>`;
            event.target.reset();
        } else {
            showToast(data.error || "Could not register you as a volunteer.");
        }
    } catch (e) {
        showToast("Could not reach Volunteer Service.");
    } finally {
        setLoading(btn, false, "", "Join the corps");
    }
});

async function signUp() {
    const btn = document.getElementById("signupBtn");
    const volunteerId = document.getElementById("volunteerId").value;
    const complaintId = document.getElementById("complaintId").value;
    if (!volunteerId || !complaintId) { showToast("Fill in both IDs first."); return; }

    setLoading(btn, true, "Signing up...");
    try {
        const response = await fetch(SIGNUP_API, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({volunteer_id: volunteerId, complaint_id: complaintId})
        });
        const data = await response.json();

        if (response.ok) {
            document.getElementById("signupResult").innerHTML = `
                <div class="ticket">
                    <div class="tid">You're in</div>
                    <div class="trow"><span>Report</span><span>${data.complaint_description}</span></div>
                    <div class="trow"><span>Location</span><span>${data.complaint_location}</span></div>
                </div>`;
        } else {
            showToast(data.error || "Could not sign you up.");
        }
    } catch (e) {
        showToast("Could not reach Volunteer Service.");
    } finally {
        setLoading(btn, false, "", "Sign me up");
    }
}

async function viewSignups() {
    const btn = document.getElementById("viewBtn");
    const id = document.getElementById("searchComplaintId").value;
    if (!id) { showToast("Enter a complaint ticket number first."); return; }

    setLoading(btn, true, "Looking up...");
    try {
        const response = await fetch(SIGNUP_API + "/complaint/" + id);
        const data = await response.json();

        const listDiv = document.getElementById("signupsList");
        if (data.length === 0) {
            listDiv.innerHTML = `<p class="empty-note">No one's signed up for this report yet — be the first.</p>`;
        } else {
            listDiv.innerHTML = data.map(s => `
                <div class="ledger-row"><span>${s.volunteer_name}</span><span>${s.volunteer_phone}</span></div>
            `).join("");
        }
    } catch (e) {
        showToast("Could not reach Volunteer Service.");
    } finally {
        setLoading(btn, false, "", "View volunteers");
    }
}
