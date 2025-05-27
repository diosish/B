import API from "./axios"
import { parseInitData } from "../utils/telegram"
import type { UserRead } from "../utils/schema"

export async function login(): Promise<UserRead> {
  const initData = parseInitData()
  const header = {
    "X-Telegram-WebApp-Data": Object.entries(initData).map(([k,v])=>`${k}=${v}`).join("\n")
  }
  const resp = await API.post<UserRead>("/auth/login", null, { headers: header })
  return resp.data
}
