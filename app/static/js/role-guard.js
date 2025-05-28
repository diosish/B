class RoleGuard {
    constructor() {
        this.tg = window.Telegram?.WebApp;
        this.currentUser = null;
        this.userRole = null;
    }

    async init() {
        if (!this.tg) {
            this.redirectToError('Приложение должно быть запущено из Telegram');
            return false;
        }

        this.currentUser = this.tg.initDataUnsafe?.user;
        if (!this.currentUser) {
            this.redirectToError('Не удалось получить данные пользователя');
            return false;
        }

        // Проверяем роль пользователя
        try {
            const response = await fetch(`/api/auth/check?telegram_id=${this.currentUser.id}`, {
                headers: {
                    'Authorization': this.tg.initData
                }
            });

            const data = await response.json();

            if (!data.registered) {
                window.location.href = '/';
                return false;
            }

            this.userRole = data.user.role;
            return true;
        } catch (error) {
            console.error('Error checking user role:', error);
            this.redirectToError('Ошибка проверки роли пользователя');
            return false;
        }
    }

    checkVolunteerAccess() {
        if (this.userRole !== 'volunteer') {
            this.redirectToError('Доступ запрещен. Эта страница только для волонтёров.');
            return false;
        }
        return true;
    }

    checkOrganizerAccess() {
        if (this.userRole !== 'organizer') {
            this.redirectToError('Доступ запрещен. Эта страница только для организаторов.');
            return false;
        }
        return true;
    }

    redirectToError(message) {
        if (this.tg && this.tg.showAlert) {
            this.tg.showAlert(message);
        }

        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    }

    redirectToCorrectProfile() {
        if (this.userRole === 'volunteer') {
            window.location.href = '/volunteer/profile';
        } else if (this.userRole === 'organizer') {
            window.location.href = '/organizer/profile';
        } else {
            window.location.href = '/';
        }
    }
}

// Создаем глобальный экземпляр
window.roleGuard = new RoleGuard();