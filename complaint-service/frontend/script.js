const API_URL = "http://localhost:5002/complaints";

function statusBadge(status) {
    const cls = status === "OPEN" ? "badge-open" : status === "RESOLVED" ? "badge-resolved" : "badge-assigned";
    return `<span class="badge ${cls}">${status}</span>`;
}

document.getElementById("complaintForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    const btn = document.getElementById("submitBtn");
    const citizenId = document.getElementById("citizenId").value;
    const description = document.getElementById("description").value;
    const location = document.getElementById("location").value;

    setLoading(btn, true, "Filing report...");
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({citizen_id: citizenId, description, location})
        });
        const data = await response.json();

        if (response.ok) {
            document.getElementById("result").innerHTML = `
                <div class="ticket">
                    <div class="tid">Ticket #${data.complaint_id}</div>
                    <div class="trow"><span>Filed by</span><span>${data.citizen_name}</span></div>
                    <div class="trow"><span>Location</span><span>${data.location}</span></div>
                    <div class="trow"><span>Status</span>${statusBadge(data.status)}</div>
                </div>`;
            event.target.reset();
        } else {
            showToast(data.error || "Could not file the report.");
        }
    } catch (e) {
        showToast("Could not reach Complaint Service.");
    } finally {
        setLoading(btn, false, "", "Submit report");
    }
});

async function findComplaint() {
    const btn = document.getElementById("trackBtn");
    const id = document.getElementById("searchComplaintId").value;
    if (!id) { showToast("Enter a complaint ID first."); return; }

    setLoading(btn, true, "Looking up...");
    try {
        const response = await fetch(API_URL + "/" + id);
        const data = await response.json();

        if (response.ok) {
            document.getElementById("complaintDetails").innerHTML = `
                <div class="ticket">
                    <div class="tid">Ticket #${data.complaint_id}</div>
                    <div class="trow"><span>Citizen ID</span><span>${data.citizen_id}</span></div>
                    <div class="trow"><span>Issue</span><span>${data.description}</span></div>
                    <div class="trow"><span>Location</span><span>${data.location}</span></div>
                    <div class="trow"><span>Status</span>${statusBadge(data.status)}</div>
                </div>`;
        } else {
            document.getElementById("complaintDetails").innerHTML = "";
            showToast(data.error || "Complaint not found.");
        }
    } catch (e) {
        showToast("Could not reach Complaint Service.");
    } finally {
        setLoading(btn, false, "", "Track report");
    }
}
