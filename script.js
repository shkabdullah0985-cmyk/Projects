// --- Signup ---
document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('name').value.trim();
            const regNum = document.getElementById('registration_number').value.trim();
            const mobile = document.getElementById('mobile').value.trim();
            const yearRadio = document.querySelector('input[name="year"]:checked');
            const password = document.getElementById('password').value.trim();

            if (!yearRadio) {
                document.getElementById('signupMessage').innerHTML = '<div style="color:red;">Please select year.</div>';
                return;
            }

            const payload = { name, registration_number: regNum, mobile, year: yearRadio.value, password };
            try {
                const res = await fetch('/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.redirect) {
                    window.location.href = data.redirect;
                } else if (data.success) {
                    document.getElementById('signupMessage').innerHTML = `<div style="color:green;">✅ ${data.message}</div>`;
                    setTimeout(() => window.location.href = '/dashboard', 1000);
                } else {
                    document.getElementById('signupMessage').innerHTML = `<div style="color:red;">❌ ${data.message}</div>`;
                }
            } catch (err) {
                document.getElementById('signupMessage').innerHTML = '<div style="color:red;">❌ Error submitting form.</div>';
            }
        });
    }

    // --- Login ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const regNum = document.getElementById('registration_number').value.trim();
            const password = document.getElementById('password').value.trim();

            const payload = { registration_number: regNum, password };
            try {
                const res = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.redirect) {
                    window.location.href = data.redirect;
                } else if (data.success) {
                    document.getElementById('loginMessage').innerHTML = `<div style="color:green;">✅ ${data.message}</div>`;
                    setTimeout(() => window.location.href = '/dashboard', 500);
                } else {
                    document.getElementById('loginMessage').innerHTML = `<div style="color:red;">❌ ${data.message}</div>`;
                }
            } catch (err) {
                document.getElementById('loginMessage').innerHTML = '<div style="color:red;">❌ Error submitting form.</div>';
            }
        });
    }

    // --- Attendance ---
    const attendanceForm = document.getElementById('attendanceForm');
    if (attendanceForm) {
        attendanceForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const regNum = document.getElementById('registration_number').value.trim();
            const yearRadio = document.querySelector('input[name="year"]:checked');
            if (!yearRadio) {
                document.getElementById('attendanceMessage').innerHTML = '<div style="color:red;">Please select year.</div>';
                return;
            }

            if (!navigator.geolocation) {
                document.getElementById('attendanceMessage').innerHTML = '<div style="color:red;">Geolocation not supported.</div>';
                return;
            }

            document.getElementById('attendanceMessage').innerHTML = '<div style="color:blue;">Fetching location...</div>';

            navigator.geolocation.getCurrentPosition(async (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const fingerprint = await getDeviceFingerprint();

                const payload = {
                    registration_number: regNum,
                    year: yearRadio.value,
                    latitude: lat,
                    longitude: lng,
                    device_fingerprint: fingerprint
                };

                try {
                    const res = await fetch('/mark_attendance', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (data.success) {
                        document.getElementById('attendanceMessage').innerHTML = `<div style="color:green;">✅ ${data.message}</div>`;
                    } else {
                        document.getElementById('attendanceMessage').innerHTML = `<div style="color:red;">❌ ${data.message}</div>`;
                    }
                } catch (err) {
                    document.getElementById('attendanceMessage').innerHTML = '<div style="color:red;">❌ Error marking attendance.</div>';
                }
            }, (error) => {
                let msg = "Location access denied. Please enable GPS.";
                if (error.code === 1) msg = "Permission denied. Allow in browser settings.";
                else if (error.code === 2) msg = "Location unavailable.";
                else if (error.code === 3) msg = "Location timed out.";
                document.getElementById('attendanceMessage').innerHTML = `<div style="color:red;">❌ ${msg}</div>`;
            });
        });
    }
});

// --- Device Fingerprint ---
async function getDeviceFingerprint() {
    try {
        const canvas = document.createElement('canvas');
        canvas.width = 200;
        canvas.height = 50;
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillStyle = '#f60';
        ctx.fillRect(125, 1, 62, 20);
        ctx.fillStyle = '#069';
        ctx.fillText('QUASTECH', 2, 15);
        ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
        ctx.fillText('Attendance', 4, 17);
        const canvasData = canvas.toDataURL();
        const userAgent = navigator.userAgent;
        const screenInfo = `${screen.width}x${screen.height}`;
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const fingerprintString = canvasData + userAgent + screenInfo + timezone;
        const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(fingerprintString));
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    } catch (e) {
        return 'fallback_' + Math.random().toString(36).substring(2, 15);
    }
}