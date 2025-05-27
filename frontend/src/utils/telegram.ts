// Распознаём и проверяем initData
export function parseInitData(): Record<string, string> {
  const data = window.Telegram.WebApp.initData || ''
  return Object.fromEntries(data.split('\n').map(p => {
    const [k, v] = p.split('=')
    return [k, v]
  }))
}
