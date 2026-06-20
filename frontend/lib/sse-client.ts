const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

export type StreamEvent =
  | {
      type: 'log'
      id?: string
      run_id: string
      node_name: string
      level: 'info' | 'warning' | 'error'
      message: string
      created_at: string
    }
  | {
      type: 'status'
      status: string
    }

export function campaignStreamPath(workspaceId: string, campaignId: string): string {
  return `${API_BASE}/workspaces/${workspaceId}/campaigns/${campaignId}/stream`
}

export async function streamCampaignLogs(
  url: string,
  getToken: () => Promise<string | null>,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const token = await getToken()
  const headers: Record<string, string> = {
    Accept: 'text/event-stream',
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(url, { headers, signal })
  if (!response.ok) {
    throw new Error(`Stream failed: ${response.status}`)
  }
  if (!response.body) {
    throw new Error('Stream response has no body')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const part of parts) {
      const line = part
        .split('\n')
        .find((l) => l.startsWith('data: '))
      if (!line) continue
      try {
        const payload = JSON.parse(line.slice(6)) as StreamEvent
        onEvent(payload)
      } catch {
        // ignore malformed frames
      }
    }
  }
}

export async function connectCampaignStream(
  url: string,
  getToken: () => Promise<string | null>,
  onEvent: (event: StreamEvent) => void,
  options?: {
    signal?: AbortSignal
    maxRetries?: number
    onConnected?: () => void
    onDisconnected?: () => void
  },
): Promise<void> {
  const maxRetries = options?.maxRetries ?? 5
  let attempt = 0

  while (attempt <= maxRetries) {
    if (options?.signal?.aborted) return
    try {
      options?.onConnected?.()
      await streamCampaignLogs(url, getToken, onEvent, options?.signal)
      options?.onDisconnected?.()
      attempt = 0
    } catch (err) {
      if (options?.signal?.aborted) return
      attempt += 1
      options?.onDisconnected?.()
      if (attempt > maxRetries) throw err
      await new Promise((r) => setTimeout(r, Math.min(1000 * 2 ** attempt, 15000)))
    }
  }
}
