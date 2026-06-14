'use client'

import { useAuth } from '@clerk/nextjs'
import { useMemo } from 'react'

import { createApiClient } from '@/lib/api-client'

export function useApiClient() {
  const { getToken } = useAuth()

  return useMemo(
    () =>
      createApiClient(async () => {
        return getToken()
      }),
    [getToken],
  )
}
