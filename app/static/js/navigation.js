class NavigationManager {
    constructor() {
        this.currentPage = null;
        this.history = [];
    }

    goToVolunteerProfile() {
        window.location.href = '/volunteer/profile';
    }

    goToVolunteerEvents() {
        window.location.href = '/volunteer/events';
    }

    goToVolunteerApplications() {
        window.location.href = '/volunteer/applications';
    }

    goToOrganizerProfile() {
        window.location.href = '/organizer/profile';
    }

    goToCreateEvent() {
        window.location.href = '/organizer/create-event';
    }

    goToOrganizerEvents() {
        window.location.href = '/organizer/events';
    }

    goToEventApplications(eventId) {
        window.location.href = `/organizer/applications?event_id=${eventId}`;
    }

    goHome() {
        window.location.href = '/';
    }

    goBack() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            this.goHome();
        }
    }

    createVolunteerMenu() {
        return `
            <div class="navigation-menu">
                <button class="nav-btn" onclick="nav.goToVolunteerProfile()">
                    👤 Профиль
                </button>
                <button class="nav-btn" onclick="nav.goToVolunteerEvents()">
                    📅 Мероприятия
                </button>
                <button class="nav-btn" onclick="nav.goToVolunteerApplications()">
                    📋 Мои заявки
                </button>
            </div>
        `;
    }

    createOrganizerMenu() {
        return `
            <div class="navigation-menu">
                <button class="nav-btn" onclick="nav.goToOrganizerProfile()">
                    👤 Профиль
                </button>
                <button class="nav-btn" onclick="nav.goToCreateEvent()">
                    ➕ Создать
                </button>
                <button class="nav-btn" onclick="nav.goToOrganizerEvents()">
                    📋 Мои события
                </button>
            </div>
        `;
    }
}

window.nav = new NavigationManager();