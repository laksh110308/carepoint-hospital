function addPatient() {
    const name = document.getElementById("name").value;
    const age = document.getElementById("age").value;
    const hr = document.getElementById("hr").value;
    const bp = document.getElementById("bp").value;
    const temp = document.getElementById("temp").value;

    fetch("http://localhost:8000/add_patient", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            age: age,
            heart_rate: hr,
            blood_pressure: bp,
            temperature: temp
        })
    })
    .then(res => res.json())
    .then(data => {
        alert("Patient Added!");
        loadPatients();
    })
    .catch(err => {
        console.error(err);
        alert("Error adding patient");
    });
}

function loadPatients() {
    fetch("http://localhost:8000/patients")
        .then(res => res.json())
        .then(data => {
            const queue = document.getElementById("queue");
            queue.innerHTML = "";

            data.forEach(p => {
                const div = document.createElement("div");
                div.className = "patient";

                div.innerHTML = `
                    <strong>${p.name}</strong><br>
                    Age: ${p.age} <br>
                    HR: ${p.heart_rate} <br>
                    BP: ${p.bp} <br>
                    Temp: ${p.temperature}
                `;

                queue.appendChild(div);
            });
        });
}

// Load on page start
window.onload = loadPatients;