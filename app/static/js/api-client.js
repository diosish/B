class APIClient {
    constructor() {
        this.baseURL = '';
        this.timeout = 30000; // 30 секунд
        this.maxRetries = 3;
        this.retryDelay = 1000; // 1 секунда
    }

    /**
     * Получение заголовков для авторизации
     */
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        const tg = window.Telegram?.WebApp;
        if (tg && tg.initData) {
            headers['Authorization'] = tg.initData;
        } else {
            headers['Authorization'] = 'test_data';
        }

        return headers;
    }

    /**
     * Выполнение HTTP запроса с retry логикой
     */
    async makeRequest(url, options = {}, retryCount = 0) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            const response = await fetch(url, {
                ...options,
                headers: {
                    ...this.getAuthHeaders(),
                    ...options.headers,
                },
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            // Логирование запроса
            console.log(`🌐 ${options.method || 'GET'} ${url} -> ${response.status}`);

            if (!response.ok) {
                const errorData = await this.parseErrorResponse(response);
                throw new APIError(errorData.message, response.status, errorData);
            }

            return response;
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new APIError('Request timeout', 408);
            }

            // Retry логика для сетевых ошибок
            if (retryCount < this.maxRetries && this.shouldRetry(error)) {
                console.warn(`🔄 Retrying request (${retryCount + 1}/${this.maxRetries}): ${url}`);
                await this.delay(this.retryDelay * (retryCount + 1));
                return this.makeRequest(url, options, retryCount + 1);
            }

            throw error;
        }
    }

    /**
     * Парсинг ошибки из ответа
     */
    async parseErrorResponse(response) {
        try {
            const errorData = await response.json();
            return {
                message: errorData.detail || `HTTP ${response.status}`,
                details: errorData,
            };
        } catch {
            return {
                message: `HTTP ${response.status}: ${response.statusText}`,
                details: null,
            };
        }
    }

    /**
     * Проверка, нужно ли повторить запрос
     */
    shouldRetry(error) {
        // Повторяем при сетевых ошибках или серверных ошибках 5xx
        return (
            error instanceof TypeError || // Сетевая ошибка
            (error instanceof APIError && error.status >= 500)
        );
    }

    /**
     * Задержка
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * GET запрос
     */
    async get(url) {
        const response = await this.makeRequest(url, { method: 'GET' });
        return response.json();
    }

    /**
     * POST запрос
     */
    async post(url, data) {
        const response = await this.makeRequest(url, {
            method: 'POST',
            body: JSON.stringify(data),
        });
        return response.json();
    }

    /**
     * PUT запрос
     */
    async put(url, data) {
        const response = await this.makeRequest(url, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
        return response.json();
    }

    /**
     * DELETE запрос
     */
    async delete(url) {
        const response = await this.makeRequest(url, { method: 'DELETE' });
        return response.json();
    }
}

// Класс для API ошибок
class APIError extends Error {
    constructor(message, status, details = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.details = details;
    }

    /**
     * Получение пользовательского сообщения об ошибке
     */
    getUserMessage() {
        switch (this.status) {
            case 400:
                return 'Некорректные данные. Проверьте введённую информацию.';
            case 401:
                return 'Необходимо войти в систему.';
            case 403:
                return 'У вас недостаточно прав для выполнения этого действия.';
            case 404:
                return 'Запрашиваемая информация не найдена.';
            case 408:
                return 'Превышено время ожидания. Попробуйте ещё раз.';
            case 409:
                return 'Конфликт данных. Возможно, информация уже существует.';
            case 429:
                return 'Слишком много запросов. Подождите немного.';
            case 500:
                return 'Ошибка сервера. Мы работаем над устранением проблемы.';
            case 503:
                return 'Сервис временно недоступен. Попробуйте позже.';
            default:
                return this.message || 'Произошла неизвестная ошибка.';
        }
    }
}

// Глобальный экземпляр API клиента
window.apiClient = new APIClient();