import React, { useEffect, useState } from 'react'
import API from '../api/axios'
import { FormRenderer } from '../components/FormRenderer'
import type { UserRead } from '../utils/schema'

export default function ProfilePage() {
  const [user, setUser] = useState<UserRead | null>(null)
  const [schema, setSchema] = useState<any>(null)

  useEffect(() => {
    API.get<UserRead>('/users/me').then(r => {
      setUser(r.data)
      return API.get(`/subtypes/${r.data.subtype_id}`)
    }).then(res => setSchema(res.data.fields_schema))
  }, [])

  if (!user || !schema) return <div>Загрузка…</div>

  return (
    <div>
      <h1>Профиль {user.full_name}</h1>
      <FormRenderer
        schema={schema}
        defaultValues={user.profile_data}
        onSubmit={data => API.patch(`/users/${user.id}`, { profile_data: data })}
      />
    </div>
  )
}
