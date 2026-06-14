'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, MoreHorizontal, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { useApiClient } from '@/hooks/use-api-client'
import { createResourceApi, queryKeys } from '@/lib/api-resources'
import { contentCreateSchema, type ContentCreateInput } from '@/lib/schemas'
import type { CampaignContent, PaginatedResponse } from '@/lib/types'
import { AppShell } from '@/components/app-shell'
import { EmptyState, PageHeader } from '@/components/page-header'
import { ContentStatusBadge, PlatformBadge } from '@/components/status-badge'
import { FieldError } from '@/components/field-error'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
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

const PLATFORMS = ['twitter', 'linkedin', 'email', 'blog'] as const
const STATUSES = ['draft', 'approved', 'rejected'] as const

function ContentCreateDialog({
  workspaceId,
  campaignId,
}: {
  workspaceId: string
  campaignId: string
}) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)

  const form = useForm<ContentCreateInput>({
    resolver: zodResolver(contentCreateSchema),
    defaultValues: { platform: 'twitter', title: '', content: '', status: 'draft' },
  })

  const mutation = useMutation({
    mutationFn: (values: ContentCreateInput) =>
      api.createContent(workspaceId, campaignId, {
        platform: values.platform,
        title: values.title || null,
        content: values.content,
        status: values.status,
      }),
    onMutate: async (values) => {
      const key = queryKeys.contents(workspaceId, campaignId)
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<PaginatedResponse<CampaignContent>>(key)
      const optimistic: CampaignContent = {
        id: `temp-${Date.now()}`,
        campaign_id: campaignId,
        platform: values.platform,
        title: values.title || null,
        content: values.content,
        status: values.status ?? 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      queryClient.setQueryData<PaginatedResponse<CampaignContent>>(key, (old) => ({
        items: [optimistic, ...(old?.items ?? [])],
        total: (old?.total ?? 0) + 1,
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.contents(workspaceId, campaignId), context.previous)
      }
      toast.error('Failed to create content')
    },
    onSuccess: () => {
      toast.success('Content created')
      setOpen(false)
      form.reset()
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.contents(workspaceId, campaignId) })
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-4" />
          Add content
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add content</DialogTitle>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Platform</Label>
              <Select
                value={form.watch('platform')}
                onValueChange={(v) => form.setValue('platform', v as ContentCreateInput['platform'])}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PLATFORMS.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={form.watch('status') ?? 'draft'}
                onValueChange={(v) => form.setValue('status', v as ContentCreateInput['status'])}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="content-title">Title</Label>
            <Input id="content-title" {...form.register('title')} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="content-body">Content</Label>
            <Textarea id="content-body" rows={6} {...form.register('content')} />
            <FieldError message={form.formState.errors.content?.message} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="size-4 animate-spin" />}
              Create
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function ContentCard({
  workspaceId,
  campaignId,
  item,
}: {
  workspaceId: string
  campaignId: string
  item: CampaignContent
}) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const isOptimistic = item.id.startsWith('temp-')

  const statusMutation = useMutation({
    mutationFn: (status: CampaignContent['status']) =>
      api.updateContent(workspaceId, campaignId, item.id, { status }),
    onMutate: async (status) => {
      const key = queryKeys.contents(workspaceId, campaignId)
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<PaginatedResponse<CampaignContent>>(key)
      queryClient.setQueryData<PaginatedResponse<CampaignContent>>(key, (old) => ({
        items:
          old?.items.map((c) => (c.id === item.id ? { ...c, status } : c)) ?? [],
        total: old?.total ?? 0,
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.contents(workspaceId, campaignId), context.previous)
      }
      toast.error('Failed to update status')
    },
    onSuccess: () => toast.success('Status updated'),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.contents(workspaceId, campaignId) })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteContent(workspaceId, campaignId, item.id),
    onMutate: async () => {
      const key = queryKeys.contents(workspaceId, campaignId)
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<PaginatedResponse<CampaignContent>>(key)
      queryClient.setQueryData<PaginatedResponse<CampaignContent>>(key, (old) => ({
        items: old?.items.filter((c) => c.id !== item.id) ?? [],
        total: Math.max(0, (old?.total ?? 1) - 1),
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.contents(workspaceId, campaignId), context.previous)
      }
      toast.error('Failed to delete content')
    },
    onSuccess: () => {
      toast.success('Content deleted')
      setConfirmOpen(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.contents(workspaceId, campaignId) })
    },
  })

  return (
    <>
      <Card className={isOptimistic ? 'opacity-60' : undefined}>
        <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0">
          <div className="min-w-0 space-y-1">
            <CardTitle className="text-base">{item.title ?? 'Untitled'}</CardTitle>
            <div className="flex flex-wrap gap-2">
              <PlatformBadge platform={item.platform} />
              <ContentStatusBadge status={item.status} />
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" disabled={isOptimistic}>
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {STATUSES.filter((s) => s !== item.status).map((status) => (
                <DropdownMenuItem
                  key={status}
                  onClick={() => statusMutation.mutate(status)}
                >
                  Mark as {status}
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem variant="destructive" onClick={() => setConfirmOpen(true)}>
                <Trash2 className="size-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardHeader>
        <CardContent>
          <CardDescription className="whitespace-pre-wrap text-sm text-foreground">
            {item.content}
          </CardDescription>
        </CardContent>
      </Card>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete content?</AlertDialogTitle>
            <AlertDialogDescription>This action cannot be undone.</AlertDialogDescription>
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

export function CampaignDetailPage({
  workspaceId,
  campaignId,
}: {
  workspaceId: string
  campaignId: string
}) {
  const client = useApiClient()
  const api = createResourceApi(client)

  const workspaceQuery = useQuery({
    queryKey: queryKeys.workspace(workspaceId),
    queryFn: () => api.getWorkspace(workspaceId),
  })

  const campaignQuery = useQuery({
    queryKey: queryKeys.campaign(workspaceId, campaignId),
    queryFn: () => api.getCampaign(workspaceId, campaignId),
    retry: (count, error) => !(isApiError(error, 404) || count > 1),
  })

  const contentsQuery = useQuery({
    queryKey: queryKeys.contents(workspaceId, campaignId),
    queryFn: () => api.listContents(workspaceId, campaignId),
    enabled: !!campaignQuery.data,
  })

  if (workspaceQuery.isLoading || campaignQuery.isLoading) {
    return (
      <AppShell workspaceId={workspaceId}>
        <Skeleton className="h-10 w-64" />
        <Skeleton className="mt-6 h-48 w-full" />
      </AppShell>
    )
  }

  if (campaignQuery.isError || !campaignQuery.data) {
    return (
      <AppShell workspaceId={workspaceId} workspaceName={workspaceQuery.data?.name}>
        <EmptyState
          title="Campaign not found"
          description="This campaign does not exist or you do not have access."
          action={
            <Button asChild variant="outline">
              <Link href={`/dashboard/workspaces/${workspaceId}`}>Back to workspace</Link>
            </Button>
          }
        />
      </AppShell>
    )
  }

  const campaign = campaignQuery.data

  return (
    <AppShell workspaceId={workspaceId} workspaceName={workspaceQuery.data?.name}>
      <div className="space-y-6">
        <PageHeader
          title={campaign.title}
          description={campaign.objective}
          breadcrumbs={[
            { label: 'Workspaces', href: '/dashboard' },
            {
              label: workspaceQuery.data?.name ?? 'Workspace',
              href: `/dashboard/workspaces/${workspaceId}`,
            },
            { label: campaign.title },
          ]}
          actions={<ContentCreateDialog workspaceId={workspaceId} campaignId={campaignId} />}
        />

        {contentsQuery.isLoading && <Skeleton className="h-32 w-full" />}
        {!contentsQuery.isLoading && contentsQuery.data?.items.length === 0 && (
          <EmptyState
            title="No content yet"
            description="Add platform-specific content for this campaign."
            action={
              <ContentCreateDialog workspaceId={workspaceId} campaignId={campaignId} />
            }
          />
        )}
        <div className="grid gap-4">
          {contentsQuery.data?.items.map((item) => (
            <ContentCard
              key={item.id}
              workspaceId={workspaceId}
              campaignId={campaignId}
              item={item}
            />
          ))}
        </div>
      </div>
    </AppShell>
  )
}
