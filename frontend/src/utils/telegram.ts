export function parseInitData(): Record<string,string> {
  const data = window.Telegram.WebApp.initData || ""
  return Object.fromEntries(data.split("\n").map(pair => {
    const [k,v] = pair.split("=")
    return [k,v]
  }))
}
