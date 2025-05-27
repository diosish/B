// frontend/src/pages/EventDetailPage.tsx
import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { EventRead } from '../utils/schema'
import API from '../api/axios'

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [event, setEvent] = useState<EventRead | null>(null)

  useEffect(() => {
    if (id) {
      API.get<EventRead>(`/events/${id}`)
        .then(r => setEvent(r.data))
        .catch(err => console.error(err))
    }
  }, [id])

  if (!event) return <div>Загрузка события…</div>

  return (
    <div>
      <h1>{event.title}</h1>
      <p>{event.description}</p>
      <p>
        Дата: {new Date(event.date_start).toLocaleString()} —{' '}
        {new Date(event.date_end).toLocaleString()}
      </p>
      <p>Оплата: {event.pay} ₽</p>
      {/* здесь можно добавить кнопку «Откликнуться» */}
    </div>
  )
}
