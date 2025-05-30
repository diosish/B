// app/static/js/navigation.js - Улучшенная система навигации

class NavigationManager {
    constructor() {
        this.currentPage = null;
        this.userRole = null;
        this.history = [];
        this.navigationMaps = {
            volunteer: [
                { id: 'profile', icon: '👤', label: 'Профиль', url: '/volunteer/profile' },
                { id: 'events', icon: '📅', label: 'Мероприятия', url: '/volunteer/events' },
                { id: 'applications', icon: '📋', label: 'Заявки', url: '/volunteer/applications' },
                { id: 'reviews', icon: '⭐', label: 'Отзывы', url: '/volunteer/reviews' }
            ],
            organizer: [
                { id: 'profile', icon: '👤', label: 'Профиль', url: '/organizer/profile' },
                { id: 'create', icon: '➕', label: 'Создать', url: '/organizer/create-event' },
                { id: 'events', icon: '📋', label: 'События', url: '/organizer/events' },
                { id: 'stats', icon: '📊', label: 'Статистика', url: '/organizer/stats' }
            ]
        };
    }

    init(userRole) {
        this.userRole = userRole;
        this.currentPage = this.getCurrentPageId();
        this.render();
        this.setupEventListeners();
    }

    getCurrentPageId() {
        const path = window.location.pathname;
        
        // Определяем текущую страницу по URL
        if (path.includes('/profile')) return 'profile';
        if (path.includes('/events')) return 'events';
        if (path.includes('/applications')) return 'applications';
        if (path.includes('/reviews')) return 'reviews';
        if (path.includes('/create')) return 'create';
        if (path.includes('/stats')) return 'stats';
        
        return null;
    }

    render() {
        const existingNav = document.querySelector('.bottom-nav');
        if (existingNav) {
            existingNav.remove();
        }

        if (!this.userRole || !this.navigationMaps[this.userRole]) {
            return;
        }

        const navItems = this.navigationMaps[this.userRole];
        const navHTML = this.createNavigationHTML(navItems);
        
        document.body.insertAdjacentHTML('beforeend', navHTML);
        this.attachClickListeners();
    }

    createNavigationHTML(navItems) {
        return `
            <nav class="bottom-nav">
                ${navItems.map(item => `
                    <a href="${item.url}" 
                       class="nav-item ${item.id === this.currentPage ? 'active' : ''}" 
                       data-page="${item.id}">
                        <span class="nav-icon">${item.icon}</span>
                        <span class="nav-label">${item.label}</span>
                    </a>
                `).join('')}
            </nav>
        `;
    }

    attachClickListeners() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const url = item.getAttribute('href');
                const pageId = item.getAttribute('data-page');
                this.navigateTo(url, pageId);
            });
        });
    }

    navigateTo(url, pageId) {
        // Добавляем в историю
        if (this.currentPage) {
            this.history.push({
                url: window.location.pathname,
                pageId: this.currentPage,
                timestamp: Date.now()
            });
        }

        // Показываем индикатор загрузки
        this.showLoadingIndicator();

        // Переходим на новую страницу
        window.location.href = url;
    }

    setupEventListeners() {
        // Обработка кнопки "Назад" браузера
        window.addEventListener('popstate', (e) => {
            const newPageId = this.getCurrentPageId();
            this.updateActiveNavItem(newPageId);
            this.currentPage = newPageId;
        });

        // Обработка жестов свайпа (для будущего улучшения)
        this.setupSwipeGestures();
    }

    setupSwipeGestures() {
        let startX = 0;
        let startY = 0;
        let endX = 0;
        let endY = 0;

        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        document.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            endY = e.changedTouches[0].clientY;
            this.handleSwipe();
        });
    }

    handleSwipe() {
        const deltaX = endX - startX;
        const deltaY = endY - startY;
        const minSwipeDistance = 100;

        // Проверяем, что это горизонтальный свайп
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > minSwipeDistance) {
            if (deltaX > 0) {
                this.navigateToPrevious();
            } else {
                this.navigateToNext();
            }
        }
    }

    navigateToPrevious() {
        const navItems = this.navigationMaps[this.userRole];
        const currentIndex = navItems.findIndex(item => item.id === this.currentPage);
        
        if (currentIndex > 0) {
            const prevItem = navItems[currentIndex - 1];
            this.navigateTo(prevItem.url, prevItem.id);
        }
    }

    navigateToNext() {
        const navItems = this.navigationMaps[this.userRole];
        const currentIndex = navItems.findIndex(item => item.id === this.currentPage);
        
        if (currentIndex < navItems.length - 1) {
            const nextItem = navItems[currentIndex + 1];
            this.navigateTo(nextItem.url, nextItem.id);
        }
    }

    updateActiveNavItem(pageId) {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            if (item.getAttribute('data-page') === pageId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    showLoadingIndicator() {
        // Создаем временный индикатор загрузки
        const loader = document.createElement('div');
        loader.className = 'page-transition-loader';
        loader.innerHTML = '<div class="loading-spinner"></div>';
        loader.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 9998;
            background: var(--tg-theme-bg-color);
            padding: var(--spacing-lg);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
        `;
        
        document.body.appendChild(loader);
        
        // Удаляем через 3 секунды (на случай если страница не загрузится)
        setTimeout(() => {
            if (loader.parentNode) {
                loader.parentNode.removeChild(loader);
            }
        }, 3000);
    }

    // Методы для быстрого доступа
    goToProfile() {
        const profileUrl = this.userRole === 'volunteer' ? '/volunteer/profile' : '/organizer/profile';
        this.navigateTo(profileUrl, 'profile');
    }

    goToEvents() {
        const eventsUrl = this.userRole === 'volunteer' ? '/volunteer/events' : '/organizer/events';
        this.navigateTo(eventsUrl, 'events');
    }

    goHome() {
        this.navigateTo('/', 'home');
    }

    goBack() {
        if (this.history.length > 0) {
            const lastPage = this.history.pop();
            window.location.href = lastPage.url;
        } else {
            this.goHome();
        }
    }

    // Утилиты для работы с навигацией
    canGoBack() {
        return this.history.length > 0;
    }

    getCurrentPageInfo() {
        if (!this.userRole || !this.currentPage) return null;
        
        const navItems = this.navigationMaps[this.userRole];
        return navItems.find(item => item.id === this.currentPage);
    }

    getNavigationStats() {
        return {
            currentPage: this.currentPage,
            userRole: this.userRole,
            historyLength: this.history.length,
            canGoBack: this.canGoBack()
        };
    }
}

// Расширенный класс для конкретных действий навигации
class QuickActions {
    constructor(navigationManager) {
        this.nav = navigationManager;
    }

    // Для волонтёров
    applyToRandomEvent() {
        this.nav.navigateTo('/volunteer/events?action=random', 'events');
    }

    checkApplications() {
        this.nav.navigateTo('/volunteer/applications?filter=pending', 'applications');
    }

    viewMyReviews() {
        this.nav.navigateTo('/volunteer/reviews', 'reviews');
    }

    // Для организаторов
    createQuickEvent() {
        this.nav.navigateTo('/organizer/create-event?quick=true', 'create');
    }

    checkPendingApplications() {
        this.nav.navigateTo('/organizer/events?filter=pending', 'events');
    }

    viewEventStats() {
        this.nav.navigateTo('/organizer/stats', 'stats');
    }

    // Общие действия
    emergencyContact() {
        const tg = window.Telegram?.WebApp;
        if (tg?.showAlert) {
            tg.showAlert('🆘 Экстренная связь:\nПоддержка: @volunteer_support_bot');
        }
    }

    shareApp() {
        const tg = window.Telegram?.WebApp;
        const shareText = 'Присоединяйся к системе волонтёров! Найди оплачиваемую работу или помощников для своего мероприятия.';
        
        if (tg?.sendData) {
            tg.sendData(JSON.stringify({
                action: 'share',
                text: shareText,
                url: window.location.origin
            }));
        } else if (navigator.share) {
            navigator.share({
                title: 'Система волонтёров',
                text: shareText,
                url: window.location.origin
            });
        }
    }
}

// Инициализация
window.addEventListener('app:ready', () => {
    // Создаем глобальные экземпляры
    window.navigation = new NavigationManager();
    window.quickActions = new QuickActions(window.navigation);
    
    // Для обратной совместимости
    window.nav = window.navigation;
    
    console.log('🧭 Navigation system initialized');
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NavigationManager, QuickActions };
}