import React, { useEffect } from 'react'
import { login } from '../api/auth'
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const nav = useNavigate()
  useEffect(() => {
    (async () => {
      try {
        const user = await login()
        // сохранить user в контексте или localStorage
        nav('/profile')
      } catch {
        alert('Не удалось авторизоваться')
      }
    })()
  }, [])

  return <div>Авторизация…</div>
}
