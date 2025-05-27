// frontend/src/pages/LoginPage.tsx
import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/auth'

export default function LoginPage() {
  const nav = useNavigate()

  useEffect(() => {
    (async () => {
      try {
        await login()
        nav('/profile')
      } catch (err) {
        console.error(err)
        alert('Не удалось авторизоваться')
      }
    })()
  }, [])

  return <div>Авторизация…</div>
}
