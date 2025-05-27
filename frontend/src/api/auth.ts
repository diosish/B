import API from './axios'
import { parseInitData } from '../utils/telegram'
import type { UserRead } from '../utils/schema'

export async function login(): Promise<UserRead> {
  const initData = parseInitData()
  const resp = await API.post<UserRead>('/auth/login', null, {
    headers: { 'X-Telegram-WebApp-Data': Object.entries(initData).map(([k,v])=>`${k}=${v}`).join('\n') }
  })
  return resp.data
}
