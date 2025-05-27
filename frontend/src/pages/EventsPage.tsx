import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import type { EventRead } from '../utils/schema'
import API from '../api/axios'

export default function EventsPage() {
  const [events, setEvents] = useState<EventRead[]>([])
  useEffect(() => {
    API.get<EventRead[]>('/events').then(r => setEvents(r.data))
  }, [])
  return (
    <div>
      <h1>Мероприятия</h1>
      {events.map(e => (
        <div key={e.id}>
          <Link to={`/events/${e.id}`}>{e.title}</Link>
          <span> ({new Date(e.date_start).toLocaleString()})</span>
        </div>
      ))}
    </div>
  )
}
