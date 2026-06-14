'use client'

import { useEffect } from 'react'

export default function GlobalError({
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
    <html lang="en">
      <body className="flex min-h-screen items-center justify-center bg-white px-4 font-sans text-neutral-900">
        <div className="w-full max-w-md space-y-6 text-center">
          <h1 className="text-2xl font-semibold">Application error</h1>
          <p className="text-sm text-neutral-600">
            A critical error occurred. Please refresh the page or try again later.
          </p>
          <button
            type="button"
            onClick={reset}
            className="inline-flex h-9 items-center rounded-md bg-neutral-900 px-4 text-sm font-medium text-white"
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  )
}
