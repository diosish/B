// Инициализация Telegram WebApp
function initTelegramWebApp() {
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;

        // Настройка WebApp
        tg.ready();
        tg.expand();

        // Применение темы Telegram
        document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';
        document.body.style.color = tg.themeParams.text_color || '#000000';

        return tg;
    }
    return null;
}

// Получение данных пользователя
function getTelegramUser() {
    const tg = window.Telegram?.WebApp;
    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
        return tg.initDataUnsafe.user;
    };
}

// Показать главную кнопку
function showMainButton(text, callback) {
    const tg = window.Telegram?.WebApp;
    if (tg && tg.MainButton) {
        tg.MainButton.text = text;
        tg.MainButton.show();
        tg.MainButton.onClick(callback);
    }
}

// Скрыть главную кнопку
function hideMainButton() {
    const tg = window.Telegram?.WebApp;
    if (tg && tg.MainButton) {
        tg.MainButton.hide();
    }
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', function() {
    initTelegramWebApp();
});