// frontend/src/pages/EventsPage.tsx
import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import type { EventRead } from '../utils/schema'
import API from '../api/axios'

export default function EventsPage() {
  const [events, setEvents] = useState<EventRead[]>([])

  useEffect(() => {
    API.get<EventRead[]>('/events')
      .then(r => setEvents(r.data))
      .catch(err => console.error(err))
  }, [])

  return (
    <div>
      <h1>Список мероприятий</h1>
      {events.length === 0 && <div>Пока нет мероприятий</div>}
      {events.map(e => (
        <div key={e.id}>
          <Link to={`/events/${e.id}`}>{e.title}</Link>
          <span> — {new Date(e.date_start).toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}
