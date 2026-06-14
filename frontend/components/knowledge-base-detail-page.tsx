'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useRef, useState } from 'react'
import { ExternalLink, Loader2, Trash2, Upload } from 'lucide-react'
import { toast } from 'sonner'

import { useApiClient } from '@/hooks/use-api-client'
import { createResourceApi, queryKeys } from '@/lib/api-resources'
import type { Document, PaginatedResponse } from '@/lib/types'
import { AppShell } from '@/components/app-shell'
import { EmptyState, PageHeader } from '@/components/page-header'
import { DocumentStatusBadge } from '@/components/status-badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { isApiError } from '@/lib/api-client'

const MAX_UPLOAD_BYTES = 20 * 1024 * 1024

function DocumentUploadButton({
  workspaceId,
  kbId,
}: {
  workspaceId: string
  kbId: string
}) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const uploaded = await api.uploadDocument(workspaceId, kbId, file)
      await api.processDocument(workspaceId, kbId, uploaded.document_id)
      return uploaded
    },
    onSuccess: () => {
      toast.success('Document uploaded and processing started')
      if (inputRef.current) {
        inputRef.current.value = ''
      }
    },
    onError: () => {
      toast.error('Failed to upload document')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents(workspaceId, kbId) })
    },
  })

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Only PDF files are supported')
      event.target.value = ''
      return
    }

    if (file.size > MAX_UPLOAD_BYTES) {
      toast.error('File must be 20 MB or smaller')
      event.target.value = ''
      return
    }

    mutation.mutate(file)
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={handleFileChange}
      />
      <Button
        size="sm"
        disabled={mutation.isPending}
        onClick={() => inputRef.current?.click()}
      >
        {mutation.isPending ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Upload className="size-4" />
        )}
        Upload PDF
      </Button>
    </>
  )
}

function DocumentRow({
  workspaceId,
  kbId,
  doc,
}: {
  workspaceId: string
  kbId: string
  doc: Document
}) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const isOptimistic = doc.id.startsWith('temp-')
  const shouldPoll = doc.status === 'pending' || doc.status === 'processing'

  const statusQuery = useQuery({
    queryKey: queryKeys.document(workspaceId, kbId, doc.id),
    queryFn: () => api.getDocument(workspaceId, kbId, doc.id),
    enabled: shouldPoll && !isOptimistic,
    refetchInterval: (query) => {
      const status = query.state.data?.status ?? doc.status
      return status === 'pending' || status === 'processing' ? 2000 : false
    },
  })

  const liveDoc = statusQuery.data ?? doc

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteDocument(workspaceId, kbId, doc.id),
    onMutate: async () => {
      const key = queryKeys.documents(workspaceId, kbId)
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<PaginatedResponse<Document>>(key)
      queryClient.setQueryData<PaginatedResponse<Document>>(key, (old) => ({
        items: old?.items.filter((d) => d.id !== doc.id) ?? [],
        total: Math.max(0, (old?.total ?? 1) - 1),
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.documents(workspaceId, kbId), context.previous)
      }
      toast.error('Failed to delete document')
    },
    onSuccess: () => {
      toast.success('Document deleted')
      setConfirmOpen(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents(workspaceId, kbId) })
    },
  })

  return (
    <>
      <Card className={isOptimistic ? 'opacity-60' : undefined}>
        <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
          <div className="min-w-0 space-y-1">
            <CardTitle className="truncate text-base">{liveDoc.file_name}</CardTitle>
            <DocumentStatusBadge status={liveDoc.status} />
          </div>
          <div className="flex shrink-0 gap-2">
            <Button variant="outline" size="sm" disabled={isOptimistic}>
              <ExternalLink className="size-4" />
              Stored locally
            </Button>
            <Button
              variant="ghost"
              size="icon"
              disabled={isOptimistic}
              onClick={() => setConfirmOpen(true)}
            >
              <Trash2 className="size-4 text-destructive" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 pt-0 text-sm text-muted-foreground">
          {liveDoc.mime_type && <p>{liveDoc.mime_type}</p>}
          {liveDoc.processing_error && (
            <p className="text-destructive">{liveDoc.processing_error}</p>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete document?</AlertDialogTitle>
            <AlertDialogDescription>
              Remove &quot;{liveDoc.file_name}&quot; from this knowledge base.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => deleteMutation.mutate()}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

function RetrieveTestPanel({ workspaceId, kbId }: { workspaceId: string; kbId: string }) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const [query, setQuery] = useState('')

  const retrieveQuery = useQuery({
    queryKey: ['retrieve', workspaceId, kbId, query],
    queryFn: () => api.retrieveChunks(workspaceId, kbId, query),
    enabled: false,
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Test retrieval</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            placeholder="Ask about brand voice..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Button
            variant="outline"
            disabled={!query.trim() || retrieveQuery.isFetching}
            onClick={() => retrieveQuery.refetch()}
          >
            {retrieveQuery.isFetching ? <Loader2 className="size-4 animate-spin" /> : 'Search'}
          </Button>
        </div>
        {retrieveQuery.data?.chunks.map((chunk) => (
          <div key={chunk.chunk_id} className="rounded-md border p-3 text-sm">
            <p className="mb-1 text-xs text-muted-foreground">
              Score {chunk.score.toFixed(3)} · chunk {chunk.chunk_index}
            </p>
            <p>{chunk.content}</p>
          </div>
        ))}
        {retrieveQuery.isError && (
          <p className="text-sm text-destructive">Retrieval failed. Check API key and indexed docs.</p>
        )}
      </CardContent>
    </Card>
  )
}

export function KnowledgeBaseDetailPage({
  workspaceId,
  kbId,
}: {
  workspaceId: string
  kbId: string
}) {
  const client = useApiClient()
  const api = createResourceApi(client)

  const workspaceQuery = useQuery({
    queryKey: queryKeys.workspace(workspaceId),
    queryFn: () => api.getWorkspace(workspaceId),
  })

  const kbQuery = useQuery({
    queryKey: queryKeys.knowledgeBase(workspaceId, kbId),
    queryFn: () => api.getKnowledgeBase(workspaceId, kbId),
    retry: (count, error) => !(isApiError(error, 404) || count > 1),
  })

  const documentsQuery = useQuery({
    queryKey: queryKeys.documents(workspaceId, kbId),
    queryFn: () => api.listDocuments(workspaceId, kbId),
    enabled: !!kbQuery.data,
  })

  if (workspaceQuery.isLoading || kbQuery.isLoading) {
    return (
      <AppShell workspaceId={workspaceId}>
        <Skeleton className="h-10 w-64" />
        <Skeleton className="mt-6 h-48 w-full" />
      </AppShell>
    )
  }

  if (kbQuery.isError || !kbQuery.data) {
    return (
      <AppShell workspaceId={workspaceId} workspaceName={workspaceQuery.data?.name}>
        <EmptyState
          title="Knowledge base not found"
          description="This knowledge base does not exist or you do not have access."
          action={
            <Button asChild variant="outline">
              <Link href={`/dashboard/workspaces/${workspaceId}?tab=knowledge`}>
                Back to workspace
              </Link>
            </Button>
          }
        />
      </AppShell>
    )
  }

  const kb = kbQuery.data

  return (
    <AppShell workspaceId={workspaceId} workspaceName={workspaceQuery.data?.name}>
      <div className="space-y-6">
        <PageHeader
          title={kb.name}
          description={`${kb.scope} scope knowledge base`}
          breadcrumbs={[
            { label: 'Workspaces', href: '/dashboard' },
            {
              label: workspaceQuery.data?.name ?? 'Workspace',
              href: `/dashboard/workspaces/${workspaceId}`,
            },
            { label: kb.name },
          ]}
          actions={<DocumentUploadButton workspaceId={workspaceId} kbId={kbId} />}
        />

        {documentsQuery.isLoading && <Skeleton className="h-32 w-full" />}
        {!documentsQuery.isLoading && documentsQuery.data?.items.length === 0 && (
          <EmptyState
            title="No documents"
            description="Upload a brand guidelines PDF to index it for campaigns."
            action={<DocumentUploadButton workspaceId={workspaceId} kbId={kbId} />}
          />
        )}
        <div className="grid gap-4">
          {documentsQuery.data?.items.map((doc) => (
            <DocumentRow
              key={doc.id}
              workspaceId={workspaceId}
              kbId={kbId}
              doc={doc}
            />
          ))}
        </div>

        {(documentsQuery.data?.items.length ?? 0) > 0 && (
          <RetrieveTestPanel workspaceId={workspaceId} kbId={kbId} />
        )}
      </div>
    </AppShell>
  )
}
