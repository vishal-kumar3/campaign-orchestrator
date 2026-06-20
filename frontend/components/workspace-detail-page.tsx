'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, MoreHorizontal, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { useApiClient } from '@/hooks/use-api-client'
import { createResourceApi, queryKeys } from '@/lib/api-resources'
import {
  campaignCreateSchema,
  knowledgeBaseCreateSchema,
  type CampaignCreateInput,
  type KnowledgeBaseCreateInput,
} from '@/lib/schemas'
import type {
  Campaign,
  KnowledgeBase,
  PaginatedResponse,
} from '@/lib/types'
import { AppShell } from '@/components/app-shell'
import { EmptyState, PageHeader } from '@/components/page-header'
import { CampaignStatusBadge, PlatformBadge, ScopeBadge } from '@/components/status-badge'
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

function CampaignCreateDialog({ workspaceId }: { workspaceId: string }) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const router = useRouter()
  const [open, setOpen] = useState(false)

  const knowledgeBasesQuery = useQuery({
    queryKey: queryKeys.knowledgeBases(workspaceId),
    queryFn: () => api.listKnowledgeBases(workspaceId),
    enabled: open,
  })

  const form = useForm<CampaignCreateInput>({
    resolver: zodResolver(campaignCreateSchema),
    defaultValues: {
      title: '',
      objective: '',
      target_audience: '',
      region: '',
      platforms: [],
      knowledge_base_id: '',
      competitor_urls: [],
    },
  })

  const mutation = useMutation({
    mutationFn: (values: CampaignCreateInput) =>
      api.createCampaign(workspaceId, {
        title: values.title,
        objective: values.objective,
        target_audience: values.target_audience || null,
        region: values.region || null,
        platforms: values.platforms?.length ? values.platforms : null,
        knowledge_base_id: values.knowledge_base_id || null,
        competitor_urls: values.competitor_urls?.length ? values.competitor_urls : null,
      }),
    onMutate: async (values) => {
      const key = queryKeys.campaigns(workspaceId)
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<PaginatedResponse<Campaign>>(key)
      const optimistic: Campaign = {
        id: `temp-${Date.now()}`,
        workspace_id: workspaceId,
        title: values.title,
        objective: values.objective,
        target_audience: values.target_audience || null,
        region: values.region || null,
        platforms: values.platforms ?? null,
        knowledge_base_id: values.knowledge_base_id || null,
        competitor_urls: values.competitor_urls ?? null,
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      queryClient.setQueryData<PaginatedResponse<Campaign>>(key, (old) => ({
        items: [optimistic, ...(old?.items ?? [])],
        total: (old?.total ?? 0) + 1,
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.campaigns(workspaceId), context.previous)
      }
      toast.error('Failed to create campaign')
    },
    onSuccess: (campaign) => {
      toast.success('Campaign created')
      setOpen(false)
      form.reset()
      router.push(`/dashboard/workspaces/${workspaceId}/campaigns/${campaign.id}`)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns(workspaceId) })
    },
  })

  const selectedPlatforms = form.watch('platforms') ?? []
  const competitorUrls = form.watch('competitor_urls') ?? []

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-4" />
          New campaign
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create campaign</DialogTitle>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
        >
          <div className="space-y-2">
            <Label htmlFor="camp-title">Title</Label>
            <Input id="camp-title" {...form.register('title')} />
            <FieldError message={form.formState.errors.title?.message} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="camp-objective">Objective</Label>
            <Textarea id="camp-objective" rows={3} {...form.register('objective')} />
            <FieldError message={form.formState.errors.objective?.message} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="camp-audience">Target audience</Label>
              <Input id="camp-audience" {...form.register('target_audience')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="camp-region">Region</Label>
              <Input id="camp-region" {...form.register('region')} />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Platforms</Label>
            <div className="flex flex-wrap gap-2">
              {PLATFORMS.map((platform) => {
                const checked = selectedPlatforms.includes(platform)
                return (
                  <Button
                    key={platform}
                    type="button"
                    size="sm"
                    variant={checked ? 'default' : 'outline'}
                    onClick={() => {
                      const next = checked
                        ? selectedPlatforms.filter((p) => p !== platform)
                        : [...selectedPlatforms, platform]
                      form.setValue('platforms', next)
                    }}
                  >
                    {platform}
                  </Button>
                )
              })}
            </div>
          </div>
          <div className="space-y-2">
            <Label>Brand knowledge base</Label>
            <Select
              value={form.watch('knowledge_base_id') || 'none'}
              onValueChange={(v) =>
                form.setValue('knowledge_base_id', v === 'none' ? '' : v)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select knowledge base" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {(knowledgeBasesQuery.data?.items ?? []).map((kb) => (
                  <SelectItem key={kb.id} value={kb.id}>
                    {kb.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FieldError message={form.formState.errors.knowledge_base_id?.message} />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Competitor URLs</Label>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={competitorUrls.length >= 5}
                onClick={() => form.setValue('competitor_urls', [...competitorUrls, ''])}
              >
                Add URL
              </Button>
            </div>
            {competitorUrls.map((_, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  placeholder="https://competitor.com"
                  {...form.register(`competitor_urls.${index}`)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() =>
                    form.setValue(
                      'competitor_urls',
                      competitorUrls.filter((__, i) => i !== index),
                    )
                  }
                >
                  <Trash2 className="size-4" />
                </Button>
              </div>
            ))}
            <FieldError message={form.formState.errors.competitor_urls?.message} />
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

function KnowledgeBaseCreateDialog({
  workspaceId,
  campaigns,
}: {
  workspaceId: string
  campaigns: Campaign[]
}) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const router = useRouter()
  const [open, setOpen] = useState(false)

  const form = useForm<KnowledgeBaseCreateInput>({
    resolver: zodResolver(knowledgeBaseCreateSchema),
    defaultValues: { name: '', scope: 'workspace', campaign_id: '' },
  })

  const scope = form.watch('scope')

  const mutation = useMutation({
    mutationFn: (values: KnowledgeBaseCreateInput) =>
      api.createKnowledgeBase(workspaceId, {
        name: values.name,
        scope: values.scope,
        campaign_id: values.scope === 'campaign' ? values.campaign_id : null,
      }),
    onMutate: async (values) => {
      const key = queryKeys.knowledgeBases(workspaceId)
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<PaginatedResponse<KnowledgeBase>>(key)
      const optimistic: KnowledgeBase = {
        id: `temp-${Date.now()}`,
        workspace_id: workspaceId,
        campaign_id: values.scope === 'campaign' ? values.campaign_id ?? null : null,
        scope: values.scope,
        name: values.name,
        created_at: new Date().toISOString(),
      }
      queryClient.setQueryData<PaginatedResponse<KnowledgeBase>>(key, (old) => ({
        items: [optimistic, ...(old?.items ?? [])],
        total: (old?.total ?? 0) + 1,
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.knowledgeBases(workspaceId), context.previous)
      }
      toast.error('Failed to create knowledge base')
    },
    onSuccess: (kb) => {
      toast.success('Knowledge base created')
      setOpen(false)
      form.reset()
      router.push(`/dashboard/workspaces/${workspaceId}/knowledge-bases/${kb.id}`)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledgeBases(workspaceId) })
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-4" />
          New knowledge base
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create knowledge base</DialogTitle>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
        >
          <div className="space-y-2">
            <Label htmlFor="kb-name">Name</Label>
            <Input id="kb-name" {...form.register('name')} />
            <FieldError message={form.formState.errors.name?.message} />
          </div>
          <div className="space-y-2">
            <Label>Scope</Label>
            <Select
              value={scope}
              onValueChange={(value: 'workspace' | 'campaign') => {
                form.setValue('scope', value)
                if (value === 'workspace') form.setValue('campaign_id', '')
              }}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="workspace">Workspace</SelectItem>
                <SelectItem value="campaign">Campaign</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {scope === 'campaign' && (
            <div className="space-y-2">
              <Label>Campaign</Label>
              <Select
                value={form.watch('campaign_id') || undefined}
                onValueChange={(value) => form.setValue('campaign_id', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select campaign" />
                </SelectTrigger>
                <SelectContent>
                  {campaigns.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FieldError message={form.formState.errors.campaign_id?.message} />
            </div>
          )}
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

function CampaignRow({
  workspaceId,
  campaign,
}: {
  workspaceId: string
  campaign: Campaign
}) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const isOptimistic = campaign.id.startsWith('temp-')

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteCampaign(workspaceId, campaign.id),
    onMutate: async () => {
      const key = queryKeys.campaigns(workspaceId)
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<PaginatedResponse<Campaign>>(key)
      queryClient.setQueryData<PaginatedResponse<Campaign>>(key, (old) => ({
        items: old?.items.filter((c) => c.id !== campaign.id) ?? [],
        total: Math.max(0, (old?.total ?? 1) - 1),
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.campaigns(workspaceId), context.previous)
      }
      toast.error('Failed to delete campaign')
    },
    onSuccess: () => {
      toast.success('Campaign deleted')
      setConfirmOpen(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns(workspaceId) })
    },
  })

  return (
    <>
      <Card className={isOptimistic ? 'opacity-60' : undefined}>
        <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0 pb-2">
          <div className="min-w-0 space-y-1">
            <CardTitle className="text-base">
              <Link
                href={`/dashboard/workspaces/${workspaceId}/campaigns/${campaign.id}`}
                className="hover:underline"
              >
                {campaign.title}
              </Link>
            </CardTitle>
            <CardDescription className="line-clamp-2">{campaign.objective}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <CampaignStatusBadge status={campaign.status} />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" disabled={isOptimistic}>
                  <MoreHorizontal className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem variant="destructive" onClick={() => setConfirmOpen(true)}>
                  <Trash2 className="size-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {campaign.platforms?.map((p) => <PlatformBadge key={p} platform={p} />)}
        </CardContent>
      </Card>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete campaign?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &quot;{campaign.title}&quot; and its contents.
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

function KnowledgeBaseRow({
  workspaceId,
  kb,
}: {
  workspaceId: string
  kb: KnowledgeBase
}) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const isOptimistic = kb.id.startsWith('temp-')

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteKnowledgeBase(workspaceId, kb.id),
    onMutate: async () => {
      const key = queryKeys.knowledgeBases(workspaceId)
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<PaginatedResponse<KnowledgeBase>>(key)
      queryClient.setQueryData<PaginatedResponse<KnowledgeBase>>(key, (old) => ({
        items: old?.items.filter((k) => k.id !== kb.id) ?? [],
        total: Math.max(0, (old?.total ?? 1) - 1),
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.knowledgeBases(workspaceId), context.previous)
      }
      toast.error('Failed to delete knowledge base')
    },
    onSuccess: () => {
      toast.success('Knowledge base deleted')
      setConfirmOpen(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledgeBases(workspaceId) })
    },
  })

  return (
    <>
      <Card className={isOptimistic ? 'opacity-60' : undefined}>
        <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0">
          <div className="min-w-0 space-y-1">
            <CardTitle className="text-base">
              <Link
                href={`/dashboard/workspaces/${workspaceId}/knowledge-bases/${kb.id}`}
                className="hover:underline"
              >
                {kb.name}
              </Link>
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <ScopeBadge scope={kb.scope} />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" disabled={isOptimistic}>
                  <MoreHorizontal className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem variant="destructive" onClick={() => setConfirmOpen(true)}>
                  <Trash2 className="size-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
      </Card>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete knowledge base?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &quot;{kb.name}&quot; and its documents.
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

export function WorkspaceDetailPage({ workspaceId }: { workspaceId: string }) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const searchParams = useSearchParams()
  const tab = searchParams.get('tab') === 'knowledge' ? 'knowledge' : 'campaigns'

  const workspaceQuery = useQuery({
    queryKey: queryKeys.workspace(workspaceId),
    queryFn: () => api.getWorkspace(workspaceId),
    retry: (count, error) => !(isApiError(error, 404) || count > 1),
  })

  const campaignsQuery = useQuery({
    queryKey: queryKeys.campaigns(workspaceId),
    queryFn: () => api.listCampaigns(workspaceId),
    enabled: !!workspaceQuery.data,
  })

  const knowledgeQuery = useQuery({
    queryKey: queryKeys.knowledgeBases(workspaceId),
    queryFn: () => api.listKnowledgeBases(workspaceId),
    enabled: !!workspaceQuery.data,
  })

  if (workspaceQuery.isLoading) {
    return (
      <AppShell workspaceId={workspaceId}>
        <Skeleton className="h-10 w-64" />
        <Skeleton className="mt-6 h-48 w-full" />
      </AppShell>
    )
  }

  if (workspaceQuery.isError || !workspaceQuery.data) {
    return (
      <AppShell>
        <EmptyState
          title="Workspace not found"
          description="This workspace does not exist or you do not have access."
          action={
            <Button asChild variant="outline">
              <Link href="/dashboard">Back to workspaces</Link>
            </Button>
          }
        />
      </AppShell>
    )
  }

  const workspace = workspaceQuery.data

  return (
    <AppShell workspaceId={workspaceId} workspaceName={workspace.name}>
      <div className="space-y-6">
        <PageHeader
          title={workspace.name}
          description={workspace.description ?? 'Manage campaigns and knowledge bases.'}
          breadcrumbs={[
            { label: 'Workspaces', href: '/dashboard' },
            { label: workspace.name },
          ]}
        />

        <Tabs value={tab}>
          <TabsList>
            <TabsTrigger value="campaigns" asChild>
              <Link href={`/dashboard/workspaces/${workspaceId}?tab=campaigns`}>Campaigns</Link>
            </TabsTrigger>
            <TabsTrigger value="knowledge" asChild>
              <Link href={`/dashboard/workspaces/${workspaceId}?tab=knowledge`}>Knowledge</Link>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="campaigns" className="space-y-4">
            <div className="flex justify-end">
              <CampaignCreateDialog workspaceId={workspaceId} />
            </div>
            {campaignsQuery.isLoading && <Skeleton className="h-32 w-full" />}
            {!campaignsQuery.isLoading && campaignsQuery.data?.items.length === 0 && (
              <EmptyState
                title="No campaigns"
                description="Create a campaign to start generating content."
                action={<CampaignCreateDialog workspaceId={workspaceId} />}
              />
            )}
            <div className="grid gap-4">
              {campaignsQuery.data?.items.map((campaign) => (
                <CampaignRow key={campaign.id} workspaceId={workspaceId} campaign={campaign} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="knowledge" className="space-y-4">
            <div className="flex justify-end">
              <KnowledgeBaseCreateDialog
                workspaceId={workspaceId}
                campaigns={campaignsQuery.data?.items ?? []}
              />
            </div>
            {knowledgeQuery.isLoading && <Skeleton className="h-32 w-full" />}
            {!knowledgeQuery.isLoading && knowledgeQuery.data?.items.length === 0 && (
              <EmptyState
                title="No knowledge bases"
                description="Add brand voice documents and reference material."
                action={
                  <KnowledgeBaseCreateDialog
                    workspaceId={workspaceId}
                    campaigns={campaignsQuery.data?.items ?? []}
                  />
                }
              />
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              {knowledgeQuery.data?.items.map((kb) => (
                <KnowledgeBaseRow key={kb.id} workspaceId={workspaceId} kb={kb} />
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  )
}
