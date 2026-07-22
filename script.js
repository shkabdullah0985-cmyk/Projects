// Toggle between forms
const attendanceBtn = document.getElementById("attendanceBtn");
const registerBtn = document.getElementById("registerBtn");
const attendanceForm = document.querySelector(".attendance");
const registerForm = document.querySelector(".register-form");

attendanceBtn.addEventListener("click", () => {
    attendanceForm.classList.add("activeForm");
    registerForm.classList.remove("activeForm");
    attendanceBtn.classList.add("active");
    registerBtn.classList.remove("active");
    document.getElementById("attendanceMessage").innerHTML = "";
});

registerBtn.addEventListener("click", () => {
    registerForm.classList.add("activeForm");
    attendanceForm.classList.remove("activeForm");
    registerBtn.classList.add("active");
    attendanceBtn.classList.remove("active");
    document.getElementById("registrationMessage").innerHTML = "";
});

// Registration
document.getElementById("registrationForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("name").value.trim();
    const regNum = document.getElementById("registrationnumber").value.trim();
    const mobile = document.getElementById("mobile").value.trim();
    const yearRadio = document.querySelector('#registrationForm input[name="year"]:checked');
    if (!yearRadio) {
        document.getElementById("registrationMessage").innerHTML = '<div style="color:red;">Please select a year.</div>';
        return;
    }
    const year = yearRadio.value;

    const payload = { name, registration_number: regNum, mobile, year };
    try {
        const res = await fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        const msgDiv = document.getElementById("registrationMessage");
        if (data.success) {
            msgDiv.innerHTML = `<div style="color:green;">✅ ${data.message}</div>`;
            document.getElementById("registrationForm").reset();
        } else {
            msgDiv.innerHTML = `<div style="color:red;">❌ ${data.message}</div>`;
        }
    } catch (err) {
        document.getElementById("registrationMessage").innerHTML = `<div style="color:red;">❌ Error submitting form.</div>`;
    }
});

// Attendance with GPS
document.getElementById("attendanceForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const student_id = document.getElementById("student_id").value.trim().toUpperCase();
    const yearRadio = document.querySelector('#attendanceForm input[name="year"]:checked');
    if (!student_id) {
        document.getElementById("attendanceMessage").innerHTML = '<div style="color:red;">Please enter Student ID.</div>';
        return;
    }
    if (!yearRadio) {
        document.getElementById("attendanceMessage").innerHTML = '<div style="color:red;">Please select a year.</div>';
        return;
    }
    const year = yearRadio.value;

    if (!navigator.geolocation) {
        document.getElementById("attendanceMessage").innerHTML = '<div style="color:red;">Geolocation not supported in this browser.</div>';
        return;
    }

    document.getElementById("attendanceMessage").innerHTML = '<div style="color:blue;">Fetching location...</div>';

    navigator.geolocation.getCurrentPosition(async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        const payload = {
            student_id,
            year,
            latitude: lat,
            longitude: lng
        };

        try {
            const res = await fetch("/mark_attendance", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            const msgDiv = document.getElementById("attendanceMessage");
            if (data.success) {
                msgDiv.innerHTML = `<div style="color:green;">✅ ${data.message}</div>`;
                document.getElementById("attendanceForm").reset();
            } else {
                msgDiv.innerHTML = `<div style="color:red;">❌ ${data.message}</div>`;
            }
        } catch (err) {
            document.getElementById("attendanceMessage").innerHTML = `<div style="color:red;">❌ Error marking attendance.</div>`;
        }
    }, (error) => {
        let msg = "Location access denied. Please enable GPS and allow location permission.";
        if (error.code === 1) msg = "Location permission denied. Please allow in browser settings.";
        else if (error.code === 2) msg = "Location unavailable. Please try again.";
        else if (error.code === 3) msg = "Location request timed out. Please try again.";
        document.getElementById("attendanceMessage").innerHTML = `<div style="color:red;">❌ ${msg}</div>`;
    }, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    });
});