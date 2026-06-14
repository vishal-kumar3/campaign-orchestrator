'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ExternalLink, Loader2, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { useApiClient } from '@/hooks/use-api-client'
import { createResourceApi, queryKeys } from '@/lib/api-resources'
import { documentCreateSchema, type DocumentCreateInput } from '@/lib/schemas'
import type { Document, PaginatedResponse } from '@/lib/types'
import { AppShell } from '@/components/app-shell'
import { EmptyState, PageHeader } from '@/components/page-header'
import { DocumentStatusBadge } from '@/components/status-badge'
import { FieldError } from '@/components/field-error'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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

function DocumentCreateDialog({
  workspaceId,
  kbId,
}: {
  workspaceId: string
  kbId: string
}) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)

  const form = useForm<DocumentCreateInput>({
    resolver: zodResolver(documentCreateSchema),
    defaultValues: { file_name: '', file_url: '', mime_type: '' },
  })

  const mutation = useMutation({
    mutationFn: (values: DocumentCreateInput) =>
      api.createDocument(workspaceId, kbId, {
        file_name: values.file_name,
        file_url: values.file_url,
        mime_type: values.mime_type || null,
      }),
    onMutate: async (values) => {
      const key = queryKeys.documents(workspaceId, kbId)
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<PaginatedResponse<Document>>(key)
      const optimistic: Document = {
        id: `temp-${Date.now()}`,
        knowledge_base_id: kbId,
        file_name: values.file_name,
        file_url: values.file_url,
        mime_type: values.mime_type || null,
        status: 'pending',
        created_at: new Date().toISOString(),
      }
      queryClient.setQueryData<PaginatedResponse<Document>>(key, (old) => ({
        items: [optimistic, ...(old?.items ?? [])],
        total: (old?.total ?? 0) + 1,
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.documents(workspaceId, kbId), context.previous)
      }
      toast.error('Failed to add document')
    },
    onSuccess: () => {
      toast.success('Document added')
      setOpen(false)
      form.reset()
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents(workspaceId, kbId) })
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-4" />
          Add document
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add document metadata</DialogTitle>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
        >
          <div className="space-y-2">
            <Label htmlFor="doc-name">File name</Label>
            <Input id="doc-name" {...form.register('file_name')} />
            <FieldError message={form.formState.errors.file_name?.message} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="doc-url">File URL</Label>
            <Input id="doc-url" type="url" placeholder="https://" {...form.register('file_url')} />
            <FieldError message={form.formState.errors.file_url?.message} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="doc-mime">MIME type</Label>
            <Input id="doc-mime" placeholder="application/pdf" {...form.register('mime_type')} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="size-4 animate-spin" />}
              Add
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
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
            <CardTitle className="truncate text-base">{doc.file_name}</CardTitle>
            <DocumentStatusBadge status={doc.status} />
          </div>
          <div className="flex shrink-0 gap-2">
            <Button variant="outline" size="sm" asChild disabled={isOptimistic}>
              <a href={doc.file_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="size-4" />
                Open
              </a>
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
        {doc.mime_type && (
          <CardContent className="pt-0 text-sm text-muted-foreground">{doc.mime_type}</CardContent>
        )}
      </Card>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete document?</AlertDialogTitle>
            <AlertDialogDescription>
              Remove &quot;{doc.file_name}&quot; from this knowledge base.
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
          actions={<DocumentCreateDialog workspaceId={workspaceId} kbId={kbId} />}
        />

        {documentsQuery.isLoading && <Skeleton className="h-32 w-full" />}
        {!documentsQuery.isLoading && documentsQuery.data?.items.length === 0 && (
          <EmptyState
            title="No documents"
            description="Add document metadata to reference in campaigns."
            action={<DocumentCreateDialog workspaceId={workspaceId} kbId={kbId} />}
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
      </div>
    </AppShell>
  )
}
