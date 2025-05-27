/// <reference types="vite/client" />
// src/global.d.ts

export {}

declare global {
  interface Window {
    Telegram: {
      WebApp: {
        initData: string
        expand: () => void
        // при необходимости добавьте другие методы/поля WebApp API
      }
    }
  }
}
