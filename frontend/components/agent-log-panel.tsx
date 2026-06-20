'use client'

import { useAuth } from '@clerk/nextjs'
import { useEffect, useRef, useState } from 'react'
import { Loader2 } from 'lucide-react'

import { campaignStreamPath, connectCampaignStream, type StreamEvent } from '@/lib/sse-client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { CampaignStatus } from '@/lib/types'

type LogEntry = StreamEvent & { type: 'log' }

const ACTIVE_STATUSES = new Set<CampaignStatus>([
  'researching',
  'generating',
  'approval_pending',
  'completed',
])

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString()
  } catch {
    return iso
  }
}

function levelVariant(level: LogEntry['level']) {
  if (level === 'error') return 'destructive' as const
  if (level === 'warning') return 'warning' as const
  return 'secondary' as const
}

export function AgentLogPanel({
  workspaceId,
  campaignId,
  campaignStatus,
  onStatusEvent,
  onConnectionChange,
}: {
  workspaceId: string
  campaignId: string
  campaignStatus: CampaignStatus
  onStatusEvent?: (status: CampaignStatus) => void
  onConnectionChange?: (connected: boolean) => void
}) {
  const { getToken } = useAuth()
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const onStatusEventRef = useRef(onStatusEvent)
  onStatusEventRef.current = onStatusEvent

  useEffect(() => {
    onConnectionChange?.(connected)
  }, [connected, onConnectionChange])

  useEffect(() => {
    if (!ACTIVE_STATUSES.has(campaignStatus)) return

    const controller = new AbortController()
    setError(null)

    connectCampaignStream(
      campaignStreamPath(workspaceId, campaignId),
      () => getToken(),
      (event) => {
        if (event.type === 'log') {
          setLogs((prev) => {
            const key = event.id ?? `${event.run_id}-${event.created_at}-${event.message}`
            if (prev.some((l) => (l.id ?? `${l.run_id}-${l.created_at}-${l.message}`) === key)) {
              return prev
            }
            return [...prev, event]
          })
        } else if (event.type === 'status') {
          onStatusEventRef.current?.(event.status as CampaignStatus)
        }
      },
      {
        signal: controller.signal,
        onConnected: () => setConnected(true),
        onDisconnected: () => setConnected(false),
      },
    ).catch((err: Error) => {
      if (!controller.signal.aborted) {
        setError(err.message)
        setConnected(false)
      }
    })

    return () => controller.abort()
  }, [workspaceId, campaignId, campaignStatus, getToken])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  if (!ACTIVE_STATUSES.has(campaignStatus)) {
    return null
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base">Agent activity</CardTitle>
          <div className="flex items-center gap-2">
            {connected ? (
              <Badge variant="success">Live</Badge>
            ) : (
              <Badge variant="secondary">
                <Loader2 className="mr-1 size-3 animate-spin" />
                Connecting
              </Badge>
            )}
          </div>
        </div>
        <CardDescription>Real-time logs from research, content, and publisher agents.</CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <p className="mb-3 text-sm text-destructive">
            Stream unavailable: {error}. Showing replayed logs only.
          </p>
        )}
        <div className="max-h-80 space-y-2 overflow-y-auto rounded-md border bg-muted/30 p-3 font-mono text-xs">
          {logs.length === 0 && (
            <p className="text-muted-foreground">Waiting for agent logs…</p>
          )}
          {logs.map((log) => (
            <div key={log.id ?? `${log.run_id}-${log.created_at}-${log.message}`} className="flex gap-2">
              <span className="shrink-0 text-muted-foreground">{formatTime(log.created_at)}</span>
              <Badge variant={levelVariant(log.level)} className="shrink-0 capitalize">
                {log.node_name}
              </Badge>
              <span className="min-w-0 whitespace-pre-wrap break-words">{log.message}</span>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </CardContent>
    </Card>
  )
}
