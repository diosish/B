// Система автоматической авторизации
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.tg = window.Telegram?.WebApp;
        this.initTelegram();
    }

    initTelegram() {
        if (this.tg) {
            this.tg.ready();
            this.tg.expand();

            // Применяем тему Telegram
            if (this.tg.themeParams) {
                this.applyTelegramTheme(this.tg.themeParams);
            }

            // Получаем данные пользователя из Telegram
            const telegramUser = this.tg.initDataUnsafe?.user;
            if (telegramUser) {
                this.currentUser = telegramUser;
                console.log('Telegram user:', telegramUser);
            } else {
                // Тестовые данные для разработки
                this.currentUser = {
                    id: 123456789,
                    first_name: 'Test',
                    last_name: 'User'
                };
                console.log('Using test user');
            }
        }
    }

    applyTelegramTheme(theme) {
        const root = document.documentElement;

        if (theme.bg_color) root.style.setProperty('--tg-theme-bg-color', theme.bg_color);
        if (theme.text_color) root.style.setProperty('--tg-theme-text-color', theme.text_color);
        if (theme.hint_color) root.style.setProperty('--tg-theme-hint-color', theme.hint_color);
        if (theme.button_color) root.style.setProperty('--tg-theme-button-color', theme.button_color);
        if (theme.button_text_color) root.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
    }

    async checkRegistration() {
        if (!this.currentUser) {
            throw new Error('No user data available');
        }

        try {
            const response = await fetch(`/api/auth/check?telegram_id=${this.currentUser.id}`);
            const data = await response.json();

            return data;
        } catch (error) {
            console.error('Error checking registration:', error);
            return { registered: false, user: null };
        }
    }

    async updateProfile(profileData) {
        if (!this.currentUser) {
            throw new Error('No user data available');
        }

        try {
            const response = await fetch(`/api/auth/profile?telegram_id=${this.currentUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(profileData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating profile:', error);
            throw error;
        }
    }

    redirectToRole(role) {
        if (role === 'volunteer') {
            window.location.href = '/volunteer/profile';
        } else if (role === 'organizer') {
            window.location.href = '/organizer/profile';
        }
    }

    showNotification(message, type = 'info') {
        if (this.tg && this.tg.showAlert) {
            this.tg.showAlert(message);
        } else {
            alert(message);
        }

        // Добавляем тактильную обратную связь
        if (this.tg && this.tg.HapticFeedback) {
            if (type === 'success') {
                this.tg.HapticFeedback.notificationOccurred('success');
            } else if (type === 'error') {
                this.tg.HapticFeedback.notificationOccurred('error');
            }
        }
    }

    setupMainButton(text, callback) {
        if (this.tg && this.tg.MainButton) {
            this.tg.MainButton.setText(text);
            this.tg.MainButton.show();
            this.tg.MainButton.onClick(callback);
        }
    }

    hideMainButton() {
        if (this.tg && this.tg.MainButton) {
            this.tg.MainButton.hide();
        }
    }
}

// Создаем глобальный экземпляр
window.authManager = new AuthManager();

// ===== app/static/js/navigation.js (новый файл) =====
// Система навигации между страницами
class NavigationManager {
    constructor() {
        this.currentPage = null;
        this.history = [];
    }

    // Навигация для волонтёров
    goToVolunteerProfile() {
        window.location.href = '/volunteer/profile';
    }

    goToVolunteerEvents() {
        window.location.href = '/volunteer/events';
    }

    goToVolunteerApplications() {
        window.location.href = '/volunteer/applications';
    }

    // Навигация для организаторов
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

    // Общие функции
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

    // Создание навигационного меню
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

// Создаем глобальный экземпляр
window.nav = new NavigationManager();