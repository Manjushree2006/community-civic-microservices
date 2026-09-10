const API_URL = "http://127.0.0.1:5001/citizens";

document.getElementById("citizenForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    const btn = document.getElementById("registerBtn");
    const name = document.getElementById("name").value;
    const ward = document.getElementById("ward").value;
    const phone = document.getElementById("phone").value;

    setLoading(btn, true, "Registering...");
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name, ward, phone})
        });
        const data = await response.json();

        if (response.ok) {
            document.getElementById("result").innerHTML = `
                <div class="stamp-wrap">
                    <div class="stamp citizens">REGISTERED</div>
                    <div class="stamp-detail">
                        <p class="big">Citizen #${data.citizen_id}</p>
                        <p>${data.name} — Ward ${data.ward}</p>
                    </div>
                </div>`;
            event.target.reset();
        } else {
            showToast(data.error || "Could not register citizen.");
        }
    } catch (e) {
        showToast("Could not reach Citizen Service.");
    } finally {
        setLoading(btn, false, "", "Register citizen");
    }
});

async function findCitizen() {
    const btn = document.getElementById("findBtn");
    const id = document.getElementById("searchId").value;
    if (!id) { showToast("Enter a citizen ID first."); return; }

    setLoading(btn, true, "Looking up...");
    try {
        const response = await fetch(API_URL + "/" + id);
        const data = await response.json();

        if (response.ok) {
            document.getElementById("citizenDetails").innerHTML = `
                <div class="ticket">
                    <div class="tid">#${data.citizen_id}</div>
                    <div class="trow"><span>Name</span><span>${data.name}</span></div>
                    <div class="trow"><span>Ward</span><span>${data.ward}</span></div>
                    <div class="trow"><span>Phone</span><span>${data.phone}</span></div>
                </div>`;
        } else {
            document.getElementById("citizenDetails").innerHTML = "";
            showToast(data.error || "Citizen not found.");
        }
    } catch (e) {
        showToast("Could not reach Citizen Service.");
    } finally {
        setLoading(btn, false, "", "Find citizen");
    }
}
