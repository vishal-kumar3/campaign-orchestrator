'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { AlertCircle } from 'lucide-react'

import { Button } from '@/components/ui/button'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="mx-auto flex max-w-lg flex-col items-center gap-6 px-4 py-16 text-center">
      <div className="flex size-14 items-center justify-center rounded-full border border-destructive/20 bg-destructive/10">
        <AlertCircle className="size-6 text-destructive" />
      </div>
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Failed to load dashboard</h2>
        <p className="text-sm text-muted-foreground">
          {error.message || 'Check your connection and try again.'}
        </p>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Button onClick={reset}>Retry</Button>
        <Button asChild variant="outline">
          <Link href="/dashboard">Back to workspaces</Link>
        </Button>
      </div>
    </div>
  )
}
