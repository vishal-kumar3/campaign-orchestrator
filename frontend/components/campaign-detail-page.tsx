'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, MoreHorizontal, Play, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { useApiClient } from '@/hooks/use-api-client'
import { createResourceApi, queryKeys } from '@/lib/api-resources'
import { contentCreateSchema, type ContentCreateInput } from '@/lib/schemas'
import type {
  Campaign,
  CampaignContent,
  CampaignStatus,
  ContentApprovalItem,
  KnowledgeBase,
  PaginatedResponse,
} from '@/lib/types'
import { AppShell } from '@/components/app-shell'
import { AgentLogPanel } from '@/components/agent-log-panel'
import { EmptyState, PageHeader } from '@/components/page-header'
import {
  CampaignStatusBadge,
  ContentStatusBadge,
  PlatformBadge,
} from '@/components/status-badge'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
const STATUSES = ['draft', 'approved', 'rejected', 'published', 'failed'] as const
const POLLING_STATUSES = new Set<CampaignStatus>(['researching', 'generating'])
const STREAM_ACTIVE_STATUSES = new Set<CampaignStatus>([
  'researching',
  'generating',
  'approval_pending',
  'completed',
])

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
  approvalMode = false,
  approvalState,
  onApprovalChange,
}: {
  workspaceId: string
  campaignId: string
  item: CampaignContent
  approvalMode?: boolean
  approvalState?: { content: string; status: 'approved' | 'rejected' }
  onApprovalChange?: (update: { content?: string; status?: 'approved' | 'rejected' }) => void
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
        items: old?.items.map((c) => (c.id === item.id ? { ...c, status } : c)) ?? [],
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
              <ContentStatusBadge
                status={(approvalState?.status ?? item.status) as CampaignContent['status']}
              />
            </div>
          </div>
          {!approvalMode && (
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
          )}
        </CardHeader>
        <CardContent className="space-y-3">
          {approvalMode ? (
            <>
              <Textarea
                rows={6}
                value={approvalState?.content ?? item.content}
                onChange={(e) => onApprovalChange?.({ content: e.target.value })}
              />
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant={approvalState?.status === 'approved' ? 'default' : 'outline'}
                  onClick={() => onApprovalChange?.({ status: 'approved' })}
                >
                  Approve
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={approvalState?.status === 'rejected' ? 'destructive' : 'outline'}
                  onClick={() => onApprovalChange?.({ status: 'rejected' })}
                >
                  Reject
                </Button>
              </div>
            </>
          ) : (
            <>
              <CardDescription className="whitespace-pre-wrap text-sm text-foreground">
                {item.content}
              </CardDescription>
              {item.external_post_id && (
                <p className="text-xs text-muted-foreground">
                  Post ID:{' '}
                  {item.external_post_id.startsWith('dry-run-') ? (
                    item.external_post_id
                  ) : (
                    <a
                      href={`https://twitter.com/i/web/status/${item.external_post_id}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary underline-offset-4 hover:underline"
                    >
                      {item.external_post_id}
                    </a>
                  )}
                </p>
              )}
            </>
          )}
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

function ApprovalPanel({
  workspaceId,
  campaignId,
  items,
  onSubmitted,
}: {
  workspaceId: string
  campaignId: string
  items: CampaignContent[]
  onSubmitted: () => void
}) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const [rejectAllToDraft, setRejectAllToDraft] = useState(false)
  const [approvals, setApprovals] = useState<
    Record<string, { content: string; status: 'approved' | 'rejected' }>
  >(() =>
    Object.fromEntries(
      items.map((item) => [item.id, { content: item.content, status: 'approved' as const }]),
    ),
  )

  useEffect(() => {
    setApprovals(
      Object.fromEntries(
        items.map((item) => [item.id, { content: item.content, status: 'approved' as const }]),
      ),
    )
  }, [items])

  const approveMutation = useMutation({
    mutationFn: (payload: ContentApprovalItem[]) =>
      api.approveCampaign(workspaceId, campaignId, {
        contents: payload,
        reject_all_to_draft: rejectAllToDraft,
      }),
    onSuccess: (data) => {
      if (data.resuming) {
        toast.success('Approval submitted — publishing approved content')
      } else if (data.status === 'draft') {
        toast.success('All content rejected — campaign returned to draft')
      } else {
        toast.success('Approval saved')
      }
      onSubmitted()
    },
    onError: () => toast.error('Failed to submit approval'),
  })

  const handleSubmit = () => {
    const payload: ContentApprovalItem[] = items.map((item) => ({
      id: item.id,
      content: approvals[item.id]?.content ?? item.content,
      status: approvals[item.id]?.status ?? 'approved',
    }))
    approveMutation.mutate(payload)
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-4 text-sm">
        Review generated content before publishing. Only approved Twitter content will be
        published in this phase; LinkedIn is saved for Phase 4.
      </div>
      <div className="grid gap-4">
        {items.map((item) => (
          <ContentCard
            key={item.id}
            workspaceId={workspaceId}
            campaignId={campaignId}
            item={item}
            approvalMode
            approvalState={approvals[item.id]}
            onApprovalChange={(update) =>
              setApprovals((prev) => ({
                ...prev,
                [item.id]: { ...prev[item.id], ...update },
              }))
            }
          />
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <input
            id="reject-all-draft"
            type="checkbox"
            className="size-4 rounded border"
            checked={rejectAllToDraft}
            onChange={(e) => setRejectAllToDraft(e.target.checked)}
          />
          <Label htmlFor="reject-all-draft" className="text-sm font-normal">
            Reject all and return campaign to draft
          </Label>
        </div>
        <Button onClick={handleSubmit} disabled={approveMutation.isPending}>
          {approveMutation.isPending && <Loader2 className="size-4 animate-spin" />}
          Submit approval
        </Button>
      </div>
    </div>
  )
}

function CampaignOverview({
  campaign,
  knowledgeBase,
}: {
  campaign: Campaign
  knowledgeBase: KnowledgeBase | undefined
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Campaign details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div>
          <p className="font-medium text-muted-foreground">Status</p>
          <div className="mt-1">
            <CampaignStatusBadge status={campaign.status} />
          </div>
        </div>
        <div>
          <p className="font-medium text-muted-foreground">Objective</p>
          <p className="mt-1 whitespace-pre-wrap">{campaign.objective}</p>
        </div>
        {campaign.target_audience && (
          <div>
            <p className="font-medium text-muted-foreground">Target audience</p>
            <p className="mt-1">{campaign.target_audience}</p>
          </div>
        )}
        {campaign.region && (
          <div>
            <p className="font-medium text-muted-foreground">Region</p>
            <p className="mt-1">{campaign.region}</p>
          </div>
        )}
        <div>
          <p className="font-medium text-muted-foreground">Platforms</p>
          <div className="mt-1 flex flex-wrap gap-2">
            {(campaign.platforms ?? []).map((p) => (
              <PlatformBadge key={p} platform={p} />
            ))}
            {!campaign.platforms?.length && (
              <span className="text-muted-foreground">None selected</span>
            )}
          </div>
        </div>
        <div>
          <p className="font-medium text-muted-foreground">Knowledge base</p>
          <p className="mt-1">
            {knowledgeBase?.name ?? (
              <span className="text-muted-foreground">Not linked</span>
            )}
          </p>
        </div>
        <div>
          <p className="font-medium text-muted-foreground">Competitor URLs</p>
          {campaign.competitor_urls?.length ? (
            <ul className="mt-1 list-inside list-disc space-y-1">
              {campaign.competitor_urls.map((url) => (
                <li key={url}>
                  <a
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary underline-offset-4 hover:underline"
                  >
                    {url}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-muted-foreground">None</p>
          )}
        </div>
      </CardContent>
    </Card>
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
  const queryClient = useQueryClient()
  const [sseConnected, setSseConnected] = useState(false)

  const workspaceQuery = useQuery({
    queryKey: queryKeys.workspace(workspaceId),
    queryFn: () => api.getWorkspace(workspaceId),
  })

  const campaignQuery = useQuery({
    queryKey: queryKeys.campaign(workspaceId, campaignId),
    queryFn: () => api.getCampaign(workspaceId, campaignId),
    retry: (count, error) => !(isApiError(error, 404) || count > 1),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (sseConnected && status && STREAM_ACTIVE_STATUSES.has(status)) {
        return false
      }
      return status && POLLING_STATUSES.has(status) ? 2000 : false
    },
  })

  const handleStatusEvent = useCallback(
    (status: CampaignStatus) => {
      queryClient.setQueryData(queryKeys.campaign(workspaceId, campaignId), (old: Campaign | undefined) =>
        old ? { ...old, status } : old,
      )
      if (status === 'approval_pending' || status === 'completed') {
        queryClient.invalidateQueries({ queryKey: queryKeys.contents(workspaceId, campaignId) })
        queryClient.invalidateQueries({
          queryKey: queryKeys.researchSnapshots(workspaceId, campaignId),
        })
      }
    },
    [campaignId, queryClient, workspaceId],
  )

  const campaign = campaignQuery.data
  const prevStatusRef = useRef(campaign?.status)

  useEffect(() => {
    if (!campaign) return
    if (
      prevStatusRef.current !== campaign.status &&
      (campaign.status === 'approval_pending' || campaign.status === 'completed')
    ) {
      queryClient.invalidateQueries({ queryKey: queryKeys.contents(workspaceId, campaignId) })
      queryClient.invalidateQueries({
        queryKey: queryKeys.researchSnapshots(workspaceId, campaignId),
      })
    }
    prevStatusRef.current = campaign.status
  }, [campaign, campaignId, queryClient, workspaceId])

  const knowledgeBasesQuery = useQuery({
    queryKey: queryKeys.knowledgeBases(workspaceId),
    queryFn: () => api.listKnowledgeBases(workspaceId),
    enabled: !!campaign?.knowledge_base_id,
  })

  const contentsQuery = useQuery({
    queryKey: queryKeys.contents(workspaceId, campaignId),
    queryFn: () => api.listContents(workspaceId, campaignId),
    enabled: !!campaign,
  })

  const researchQuery = useQuery({
    queryKey: queryKeys.researchSnapshots(workspaceId, campaignId),
    queryFn: () => api.listResearchSnapshots(workspaceId, campaignId),
    enabled: !!campaign && campaign.status !== 'draft',
  })

  const executeMutation = useMutation({
    mutationFn: () => api.executeCampaign(workspaceId, campaignId),
    onSuccess: () => {
      toast.success('Campaign execution started')
      queryClient.invalidateQueries({ queryKey: queryKeys.campaign(workspaceId, campaignId) })
    },
    onError: () => toast.error('Failed to start campaign execution'),
  })

  if (workspaceQuery.isLoading || campaignQuery.isLoading) {
    return (
      <AppShell workspaceId={workspaceId}>
        <Skeleton className="h-10 w-64" />
        <Skeleton className="mt-6 h-48 w-full" />
      </AppShell>
    )
  }

  if (campaignQuery.isError || !campaign) {
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

  const knowledgeBase = knowledgeBasesQuery.data?.items.find(
    (kb) => kb.id === campaign.knowledge_base_id,
  )
  const latestResearch = researchQuery.data?.items[0]
  const canRun =
    campaign.status === 'draft' &&
    !!campaign.knowledge_base_id &&
    !executeMutation.isPending
  const isRunning = POLLING_STATUSES.has(campaign.status)

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
          actions={
            <div className="flex flex-wrap items-center gap-2">
              <CampaignStatusBadge status={campaign.status} />
              <Button
                size="sm"
                disabled={!canRun}
                onClick={() => executeMutation.mutate()}
              >
                {executeMutation.isPending || isRunning ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Play className="size-4" />
                )}
                Run campaign
              </Button>
              <ContentCreateDialog workspaceId={workspaceId} campaignId={campaignId} />
            </div>
          }
        />

        {!campaign.knowledge_base_id && campaign.status === 'draft' && (
          <p className="text-sm text-muted-foreground">
            Link a knowledge base with an indexed brand PDF before running this campaign.
          </p>
        )}

        <Tabs defaultValue="overview">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="research">Research</TabsTrigger>
            <TabsTrigger value="content">Content</TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-4">
            <CampaignOverview campaign={campaign} knowledgeBase={knowledgeBase} />
          </TabsContent>

          <TabsContent value="research" className="mt-4 space-y-4">
            {researchQuery.isLoading && <Skeleton className="h-32 w-full" />}
            {!researchQuery.isLoading && !latestResearch && (
              <EmptyState
                title="No research yet"
                description="Run the campaign to generate a research snapshot."
              />
            )}
            {latestResearch && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Latest research</CardTitle>
                  <CardDescription>
                    Generated {new Date(latestResearch.created_at).toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="whitespace-pre-wrap text-sm">{latestResearch.summary}</p>
                  {latestResearch.raw_data && (
                    <details className="text-sm">
                      <summary className="cursor-pointer text-muted-foreground">
                        Raw research data
                      </summary>
                      <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-muted p-3 text-xs">
                        {JSON.stringify(latestResearch.raw_data, null, 2)}
                      </pre>
                    </details>
                  )}
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="content" className="mt-4 space-y-4">
            {campaign.status === 'approval_pending' && (contentsQuery.data?.items.length ?? 0) > 0 ? (
              <ApprovalPanel
                workspaceId={workspaceId}
                campaignId={campaignId}
                items={contentsQuery.data?.items ?? []}
                onSubmitted={() => {
                  queryClient.invalidateQueries({
                    queryKey: queryKeys.campaign(workspaceId, campaignId),
                  })
                  queryClient.invalidateQueries({
                    queryKey: queryKeys.contents(workspaceId, campaignId),
                  })
                }}
              />
            ) : (
              <>
                {contentsQuery.isLoading && <Skeleton className="h-32 w-full" />}
                {!contentsQuery.isLoading && contentsQuery.data?.items.length === 0 && (
                  <EmptyState
                    title="No content yet"
                    description="Run the campaign or add platform-specific content manually."
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
              </>
            )}
          </TabsContent>

          <TabsContent value="activity" className="mt-4">
            <AgentLogPanel
              workspaceId={workspaceId}
              campaignId={campaignId}
              campaignStatus={campaign.status}
              onStatusEvent={handleStatusEvent}
              onConnectionChange={setSseConnected}
            />
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  )
}
