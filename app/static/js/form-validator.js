class FormValidator {
    constructor() {
        this.rules = {
            required: (value) => value && value.toString().trim() !== '',
            email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            phone: (value) => /^\+?[\d\s\-\(\)]{10,}$/.test(value),
            minLength: (value, min) => value && value.length >= min,
            maxLength: (value, max) => value && value.length <= max,
            number: (value) => !isNaN(value) && isFinite(value),
            positiveNumber: (value) => !isNaN(value) && parseFloat(value) > 0,
            inn: (value) => /^\d{10,12}$/.test(value?.replace(/\s/g, '')),
        };

        this.messages = {
            required: 'Это поле обязательно для заполнения',
            email: 'Введите корректный email адрес',
            phone: 'Введите корректный номер телефона',
            minLength: (min) => `Минимум ${min} символов`,
            maxLength: (max) => `Максимум ${max} символов`,
            number: 'Введите число',
            positiveNumber: 'Введите положительное число',
            inn: 'ИНН должен содержать 10-12 цифр',
        };
    }

    /**
     * Валидация поля по правилам
     */
    validateField(value, rules) {
        const errors = [];

        for (const rule of rules) {
            if (typeof rule === 'string') {
                // Простое правило: required, email, etc.
                if (!this.rules[rule](value)) {
                    errors.push(this.messages[rule]);
                }
            } else if (typeof rule === 'object') {
                // Правило с параметрами: {type: 'minLength', value: 3}
                const { type, value: ruleValue } = rule;
                if (!this.rules[type](value, ruleValue)) {
                    const message = typeof this.messages[type] === 'function'
                        ? this.messages[type](ruleValue)
                        : this.messages[type];
                    errors.push(message);
                }
            }
        }

        return errors;
    }

    /**
     * Валидация формы
     */
    validateForm(formData, schema) {
        const errors = {};

        for (const [fieldName, rules] of Object.entries(schema)) {
            const fieldErrors = this.validateField(formData[fieldName], rules);
            if (fieldErrors.length > 0) {
                errors[fieldName] = fieldErrors;
            }
        }

        return {
            isValid: Object.keys(errors).length === 0,
            errors,
        };
    }

    /**
     * Отображение ошибок в форме
     */
    displayErrors(errors) {
        // Очищаем предыдущие ошибки
        this.clearErrors();

        for (const [fieldName, fieldErrors] of Object.entries(errors)) {
            const field = document.getElementById(fieldName);
            if (field) {
                // Добавляем класс ошибки
                field.classList.add('is-invalid');

                // Создаем элемент с ошибкой
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = fieldErrors[0]; // Показываем первую ошибку

                // Вставляем после поля
                field.parentNode.insertBefore(errorDiv, field.nextSibling);
            }
        }
    }

    /**
     * Очистка ошибок
     */
    clearErrors() {
        // Удаляем классы ошибок
        document.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });

        // Удаляем сообщения об ошибках
        document.querySelectorAll('.invalid-feedback').forEach(error => {
            error.remove();
        });
    }

    /**
     * Валидация в реальном времени
     */
    setupRealTimeValidation(formId, schema) {
        const form = document.getElementById(formId);
        if (!form) return;

        for (const fieldName of Object.keys(schema)) {
            const field = document.getElementById(fieldName);
            if (field) {
                field.addEventListener('blur', () => {
                    const value = field.value;
                    const rules = schema[fieldName];
                    const errors = this.validateField(value, rules);

                    // Очищаем ошибки для этого поля
                    field.classList.remove('is-invalid');
                    const existingError = field.parentNode.querySelector('.invalid-feedback');
                    if (existingError) {
                        existingError.remove();
                    }

                    // Показываем ошибку если есть
                    if (errors.length > 0) {
                        field.classList.add('is-invalid');
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'invalid-feedback';
                        errorDiv.textContent = errors[0];
                        field.parentNode.insertBefore(errorDiv, field.nextSibling);
                    }
                });
            }
        }
    }
}

// Глобальный экземпляр валидатора
window.formValidator = new FormValidator();
