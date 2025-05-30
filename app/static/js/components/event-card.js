// app/static/js/components/event-card.js - Улучшенный компонент карточки мероприятия

class EventCard {
    constructor(eventData, options = {}) {
        this.event = eventData;
        this.options = {
            showActions: true,
            showStatus: true,
            showOrganizer: false,
            compact: false,
            userRole: 'volunteer',
            applicationStatus: null,
            ...options
        };
    }

    render() {
        const cardClass = this.getCardClass();
        const statusBadge = this.renderStatusBadge();
        const eventInfo = this.renderEventInfo();
        const eventDescription = this.renderDescription();
        const organizerInfo = this.renderOrganizerInfo();
        const actions = this.renderActions();
        const tags = this.renderTags();

        return `
            <article class="card event-card ${cardClass}" data-event-id="${this.event.id}">
                <div class="card-header">
                    <div class="event-header-content">
                        <h3 class="event-title">${this.escapeHtml(this.event.title)}</h3>
                        ${statusBadge}
                    </div>
                    <div class="event-payment">
                        <span class="payment-amount">${this.formatMoney(this.event.payment)}</span>
                        <span class="payment-label">₽</span>
                    </div>
                </div>

                <div class="card-body">
                    ${eventInfo}
                    ${tags}
                    ${eventDescription}
                    ${organizerInfo}
                </div>

                ${actions ? `<div class="card-footer">${actions}</div>` : ''}
            </article>
        `;
    }

    getCardClass() {
        let classes = [];

        if (this.options.compact) classes.push('event-card-compact');
        if (this.event.status) classes.push(`event-card-${this.event.status}`);
        if (this.options.applicationStatus) classes.push(`application-${this.options.applicationStatus}`);

        return classes.join(' ');
    }

    renderStatusBadge() {
        if (!this.options.showStatus || !this.event.status) return '';

        const statusConfig = {
            active: { icon: '🟢', text: 'Активно', class: 'badge-active' },
            completed: { icon: '⚪', text: 'Завершено', class: 'badge-completed' },
            cancelled: { icon: '🔴', text: 'Отменено', class: 'badge-cancelled' }
        };

        const config = statusConfig[this.event.status] || statusConfig.active;

        return `
            <div class="badge ${config.class}">
                <span>${config.icon}</span>
                <span>${config.text}</span>
            </div>
        `;
    }

    renderEventInfo() {
        const infoItems = [
            { icon: '📍', value: this.event.city || 'Не указан', label: 'Город' },
            { icon: '📅', value: this.formatDate(this.event.date), label: 'Дата' },
            { icon: '⏰', value: this.formatDuration(this.event.duration), label: 'Длительность' },
            { icon: '🏷️', value: this.event.work_type || 'Не указан', label: 'Тип работы' }
        ].filter(item => item.value && item.value !== 'Не указан');

        return `
            <div class="event-info-grid">
                ${infoItems.map(item => `
                    <div class="info-item" title="${item.label}">
                        <span class="info-icon">${item.icon}</span>
                        <span class="info-value">${item.value}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderTags() {
        const tags = [];

        if (this.event.payment && this.event.payment > 0) {
            tags.push({ text: `${this.event.payment} ₽`, class: 'tag-payment' });
        }

        if (this.event.work_type) {
            tags.push({ text: this.event.work_type, class: 'tag-work-type' });
        }

        if (this.isUrgent()) {
            tags.push({ text: 'Срочно', class: 'tag-urgent' });
        }

        if (this.isHighPaying()) {
            tags.push({ text: 'Высокая оплата', class: 'tag-high-pay' });
        }

        if (tags.length === 0) return '';

        return `
            <div class="event-tags">
                ${tags.map(tag => `
                    <span class="tag ${tag.class}">${tag.text}</span>
                `).join('')}
            </div>
        `;
    }

    renderDescription() {
        if (!this.event.description) return '';

        const maxLength = this.options.compact ? 100 : 200;
        const description = this.event.description.length > maxLength
            ? this.event.description.substring(0, maxLength) + '...'
            : this.event.description;

        return `
            <div class="event-description">
                <p>${this.escapeHtml(description)}</p>
                ${this.event.description.length > maxLength ?
                    '<button class="btn-text expand-description">Читать далее</button>' : ''
                }
            </div>
        `;
    }

    renderOrganizerInfo() {
        if (!this.options.showOrganizer || !this.event.organizer) return '';

        return `
            <div class="organizer-info">
                <div class="organizer-avatar">
                    <span class="avatar-icon">🏢</span>
                </div>
                <div class="organizer-details">
                    <div class="organizer-name">${this.escapeHtml(this.event.organizer.full_name)}</div>
                    <div class="organizer-type">${this.event.organizer.org_type || 'Организатор'}</div>
                </div>
            </div>
        `;
    }

    renderActions() {
        if (!this.options.showActions) return '';

        if (this.options.userRole === 'volunteer') {
            return this.renderVolunteerActions();
        } else if (this.options.userRole === 'organizer') {
            return this.renderOrganizerActions();
        }

        return '';
    }

    renderVolunteerActions() {
        const applicationStatus = this.options.applicationStatus;

        if (applicationStatus === 'pending') {
            return `
                <div class="action-buttons">
                    <button class="btn btn-secondary btn-full" disabled>
                        ⏳ Заявка на рассмотрении
                    </button>
                    <button class="btn btn-ghost btn-sm" onclick="eventActions.withdrawApplication(${this.event.id})">
                        Отозвать заявку
                    </button>
                </div>
            `;
        } else if (applicationStatus === 'approved') {
            return `
                <div class="action-buttons">
                    <button class="btn btn-success btn-full" disabled>
                        ✅ Заявка одобрена
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="eventActions.viewDetails(${this.event.id})">
                        Подробности
                    </button>
                </div>
            `;
        } else if (applicationStatus === 'rejected') {
            return `
                <div class="action-buttons">
                    <button class="btn btn-danger btn-full" disabled>
                        ❌ Заявка отклонена
                    </button>
                </div>
            `;
        } else if (this.event.status === 'active') {
            return `
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="eventActions.apply(${this.event.id})">
                        ✋ Откликнуться
                    </button>
                    <button class="btn btn-ghost" onclick="eventActions.viewDetails(${this.event.id})">
                        👁️ Подробнее
                    </button>
                </div>
            `;
        } else {
            return `
                <div class="action-buttons">
                    <button class="btn btn-secondary btn-full" disabled>
                        ${this.event.status === 'completed' ? '⚪ Завершено' : '🔴 Отменено'}
                    </button>
                </div>
            `;
        }
    }

    renderOrganizerActions() {
        const actions = [];

        if (this.event.status === 'active') {
            actions.push(`
                <button class="btn btn-primary btn-sm" onclick="eventActions.manageApplications(${this.event.id})">
                    📋 Заявки
                </button>
            `);

            actions.push(`
                <button class="btn btn-secondary btn-sm" onclick="eventActions.editEvent(${this.event.id})">
                    ✏️ Изменить
                </button>
            `);
        }

        if (this.event.status === 'completed') {
            actions.push(`
                <button class="btn btn-warning btn-sm" onclick="eventActions.manageReviews(${this.event.id})">
                    ⭐ Отзывы
                </button>
            `);
        }

        actions.push(`
            <button class="btn btn-ghost btn-sm" onclick="eventActions.viewStats(${this.event.id})">
                📊 Статистика
            </button>
        `);

        return `
            <div class="action-buttons">
                ${actions.join('')}
            </div>
        `;
    }

    // Утилиты
    formatMoney(amount) {
        if (!amount || amount === 0) return '0';
        return new Intl.NumberFormat('ru-RU').format(amount);
    }

    formatDate(dateString) {
        if (!dateString) return 'Гибкая дата';
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatDuration(hours) {
        if (!hours) return 'Не указана';
        if (hours === 1) return '1 час';
        if (hours < 5) return `${hours} часа`;
        return `${hours} часов`;
    }

    isUrgent() {
        if (!this.event.date) return false;
        const eventDate = new Date(this.event.date);
        const now = new Date();
        const hoursUntilEvent = (eventDate - now) / (1000 * 60 * 60);
        return hoursUntilEvent > 0 && hoursUntilEvent < 24;
    }

    isHighPaying() {
        return this.event.payment && this.event.payment > 3000;
    }

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Класс для управления действиями с мероприятиями
class EventActions {
    constructor() {
        this.app = window.app;
    }

    async apply(eventId) {
        try {
            await this.app.apiRequest('/api/volunteers/apply', {
                method: 'POST',
                body: JSON.stringify({ event_id: eventId })
            });

            this.app.showSuccess('Заявка подана успешно!');

            // Обновляем карточку
            this.updateEventCard(eventId, 'pending');

        } catch (error) {
            console.error('Error applying to event:', error);
            this.app.showError(error.message);
        }
    }

    async withdrawApplication(eventId) {
        const confirmed = confirm('Отозвать заявку?\n\nВы сможете подать заявку снова позже.');
        if (!confirmed) return;

        try {
            // Здесь нужно получить ID заявки
            const applications = await this.app.apiRequest(`/api/applications/my`);
            const application = applications.find(app => app.event_id === eventId);

            if (application) {
                await this.app.apiRequest(`/api/applications/${application.id}`, {
                    method: 'DELETE'
                });

                this.app.showSuccess('Заявка отозвана');
                this.updateEventCard(eventId, null);
            }

        } catch (error) {
            console.error('Error withdrawing application:', error);
            this.app.showError(error.message);
        }
    }

    viewDetails(eventId) {
        window.location.href = `/event/${eventId}`;
    }

    manageApplications(eventId) {
        window.location.href = `/organizer/applications?event_id=${eventId}`;
    }

    editEvent(eventId) {
        window.location.href = `/organizer/edit?event_id=${eventId}`;
    }

    manageReviews(eventId) {
        window.location.href = `/organizer/reviews?event_id=${eventId}`;
    }

    viewStats(eventId) {
        window.location.href = `/organizer/manage?event_id=${eventId}`;
    }

    updateEventCard(eventId, newApplicationStatus) {
        const card = document.querySelector(`[data-event-id="${eventId}"]`);
        if (card) {
            // Перерисовываем карточку с новым статусом
            const eventData = this.getEventDataFromCard(card);
            const newCard = new EventCard(eventData, {
                applicationStatus: newApplicationStatus,
                userRole: 'volunteer'
            });

            card.outerHTML = newCard.render();
            this.attachEventListeners();
        }
    }

    getEventDataFromCard(card) {
        // Извлекаем данные события из DOM (упрощенная версия)
        return {
            id: parseInt(card.dataset.eventId),
            title: card.querySelector('.event-title').textContent,
            // ... другие поля
        };
    }

    attachEventListeners() {
        // Обработчик для кнопки "Читать далее"
        document.querySelectorAll('.expand-description').forEach(btn => {
            btn.addEventListener('click', this.expandDescription.bind(this));
        });
    }

    expandDescription(event) {
        const button = event.target;
        const card = button.closest('.event-card');
        const eventId = card.dataset.eventId;

        // Показываем полное описание в модальном окне или расширяем карточку
        // Это можно реализовать позже
        console.log('Expand description for event:', eventId);
    }
}

// Инициализация
window.addEventListener('app:ready', () => {
    window.EventCard = EventCard;
    window.eventActions = new EventActions();
    window.eventActions.attachEventListeners();
});

// Утилита для создания списка событий
class EventsList {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.getElementById(container) : container;
        this.options = {
            userRole: 'volunteer',
            showFilters: true,
            emptyMessage: 'Нет доступных мероприятий',
            ...options
        };
        this.events = [];
        this.filters = {};
    }

    render(events) {
        this.events = events;

        if (events.length === 0) {
            this.renderEmptyState();
            return;
        }

        const eventsHTML = events.map(event => {
            const card = new EventCard(event, this.options);
            return card.render();
        }).join('');

        this.container.innerHTML = eventsHTML;
        window.eventActions?.attachEventListeners();
    }

    renderEmptyState() {
        this.container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>Нет мероприятий</h3>
                <p>${this.options.emptyMessage}</p>
            </div>
        `;
    }

    filter(filters) {
        this.filters = { ...this.filters, ...filters };
        let filteredEvents = this.events;

        // Применяем фильтры
        if (filters.city) {
            filteredEvents = filteredEvents.filter(event =>
                event.city && event.city.toLowerCase().includes(filters.city.toLowerCase())
            );
        }

        if (filters.workType) {
            filteredEvents = filteredEvents.filter(event => event.work_type === filters.workType);
        }

        if (filters.minPayment) {
            filteredEvents = filteredEvents.filter(event =>
                event.payment && event.payment >= filters.minPayment
            );
        }

        this.render(filteredEvents);
    }
}

window.EventsList = EventsList;