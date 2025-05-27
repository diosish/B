export interface UserRead {
  id: string
  tg_id: number
  full_name: string
  city: string | null
  role: "volunteer" | "organizer" | "admin"
  subtype_id: string | null
  profile_data: Record<string, any>
}
export interface EventRead {
  id: string
  title: string
  description: string
  city: string
  date_start: string
  date_end: string
  pay: number
  work_class: string
  organizer_id: string
}

export interface ApplicationRead {
  id: string
  volunteer_id: string
  event_id: string
  status: "pending" | "approved" | "rejected"
}
