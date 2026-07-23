document.addEventListener('DOMContentLoaded', function() {
    // --- Settings Dropdown ---
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsDropdown = document.getElementById('settingsDropdown');
    let dropdownOpen = false;

    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            dropdownOpen = !dropdownOpen;
            settingsDropdown.style.display = dropdownOpen ? 'block' : 'none';
        });
    }

    // --- Theme Toggle ---
    const themeBtn = document.getElementById('themeBtn');
    const themeOptions = document.getElementById('themeOptions');

    if (themeBtn) {
        themeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isVisible = themeOptions.style.display === 'block';
            themeOptions.style.display = isVisible ? 'none' : 'block';
        });
    }

    document.querySelectorAll('.theme-option').forEach(btn => {
        btn.addEventListener('click', function() {
            const theme = this.dataset.theme;
            document.body.classList.toggle('dark-theme', theme === 'dark');
            localStorage.setItem('theme', theme);
            themeOptions.style.display = 'none';
        });
    });

    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }

    // --- Calendar ---
    const calendarBtn = document.getElementById('calendarBtn');
    const calendarContainer = document.getElementById('calendarContainer');

    if (calendarBtn) {
        calendarBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isVisible = calendarContainer.style.display === 'block';
            calendarContainer.style.display = isVisible ? 'none' : 'block';
            if (!isVisible) {
                loadCalendar();
            }
        });
    }

    let currentMonth = new Date().getMonth();
    let currentYear = new Date().getFullYear();

    document.getElementById('prevMonth')?.addEventListener('click', function(e) {
        e.stopPropagation();
        currentMonth--;
        if (currentMonth < 0) { currentMonth = 11; currentYear--; }
        loadCalendar(currentYear, currentMonth);
    });

    document.getElementById('nextMonth')?.addEventListener('click', function(e) {
        e.stopPropagation();
        currentMonth++;
        if (currentMonth > 11) { currentMonth = 0; currentYear++; }
        loadCalendar(currentYear, currentMonth);
    });

    function loadCalendar(year, month) {
        if (year === undefined) year = currentYear;
        if (month === undefined) month = currentMonth;

        document.getElementById('calendarMonth').textContent = 
            new Date(year, month).toLocaleString('default', { month: 'long', year: 'numeric' });

        const grid = document.getElementById('calendarGrid');
        grid.innerHTML = '';

        // Fetch attendance data
        fetch(`/calendar_data?year=${year}&month=${month+1}`)
            .then(res => res.json())
            .then(data => {
                if (!data.success) return;
                const attendance = data.data;

                const firstDay = new Date(year, month, 1).getDay();
                const daysInMonth = new Date(year, month + 1, 0).getDate();

                const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                dayNames.forEach(name => {
                    const header = document.createElement('div');
                    header.textContent = name;
                    header.style.fontWeight = 'bold';
                    header.style.textAlign = 'center';
                    header.style.padding = '5px';
                    grid.appendChild(header);
                });

                for (let i = 0; i < firstDay; i++) {
                    const empty = document.createElement('div');
                    empty.style.padding = '10px';
                    grid.appendChild(empty);
                }

                for (let day = 1; day <= daysInMonth; day++) {
                    const cell = document.createElement('div');
                    cell.className = 'calendar-day';
                    cell.textContent = day;

                    const dateObj = new Date(year, month, day);
                    if (dateObj.getDay() === 0) {
                        cell.classList.add('Sunday');
                    } else if (attendance[String(day)]) {
                        const status = attendance[String(day)];
                        if (status === 'Present' || status === 'Late') {
                            cell.classList.add('Present');
                        } else if (status === 'Absent') {
                            cell.classList.add('Absent');
                        }
                    } else {
                        cell.classList.add('other-month');
                    }
                    grid.appendChild(cell);
                }
            });
    }
});