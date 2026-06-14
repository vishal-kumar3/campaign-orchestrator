'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, MoreHorizontal, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { useApiClient } from '@/hooks/use-api-client'
import { createResourceApi, queryKeys } from '@/lib/api-resources'
import { workspaceCreateSchema, type WorkspaceCreateInput } from '@/lib/schemas'
import type { PaginatedResponse, Workspace } from '@/lib/types'
import { AppShell } from '@/components/app-shell'
import { EmptyState, PageHeader } from '@/components/page-header'
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

function WorkspaceCreateDialog() {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const router = useRouter()
  const [open, setOpen] = useState(false)

  const form = useForm<WorkspaceCreateInput>({
    resolver: zodResolver(workspaceCreateSchema),
    defaultValues: { name: '', description: '' },
  })

  const mutation = useMutation({
    mutationFn: (values: WorkspaceCreateInput) =>
      api.createWorkspace({
        name: values.name,
        description: values.description || null,
      }),
    onMutate: async (values) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.workspaces })
      const previous = queryClient.getQueryData<PaginatedResponse<Workspace>>(queryKeys.workspaces)
      const optimistic: Workspace = {
        id: `temp-${Date.now()}`,
        owner_id: '',
        name: values.name,
        description: values.description || null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      queryClient.setQueryData<PaginatedResponse<Workspace>>(queryKeys.workspaces, (old) => ({
        items: [optimistic, ...(old?.items ?? [])],
        total: (old?.total ?? 0) + 1,
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.workspaces, context.previous)
      }
      toast.error('Failed to create workspace')
    },
    onSuccess: (workspace) => {
      toast.success('Workspace created')
      setOpen(false)
      form.reset()
      router.push(`/dashboard/workspaces/${workspace.id}`)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workspaces })
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" />
          New workspace
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create workspace</DialogTitle>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
        >
          <div className="space-y-2">
            <Label htmlFor="ws-name">Name</Label>
            <Input id="ws-name" {...form.register('name')} />
            <FieldError message={form.formState.errors.name?.message} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="ws-desc">Description</Label>
            <Textarea id="ws-desc" rows={3} {...form.register('description')} />
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

function WorkspaceCard({ workspace }: { workspace: Workspace }) {
  const client = useApiClient()
  const api = createResourceApi(client)
  const queryClient = useQueryClient()
  const router = useRouter()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const isOptimistic = workspace.id.startsWith('temp-')

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteWorkspace(workspace.id),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: queryKeys.workspaces })
      const previous = queryClient.getQueryData<PaginatedResponse<Workspace>>(queryKeys.workspaces)
      queryClient.setQueryData<PaginatedResponse<Workspace>>(queryKeys.workspaces, (old) => ({
        items: old?.items.filter((w) => w.id !== workspace.id) ?? [],
        total: Math.max(0, (old?.total ?? 1) - 1),
      }))
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.workspaces, context.previous)
      }
      toast.error('Failed to delete workspace')
    },
    onSuccess: () => {
      toast.success('Workspace deleted')
      setConfirmOpen(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workspaces })
    },
  })

  return (
    <>
      <Card className={isOptimistic ? 'opacity-60' : undefined}>
        <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0">
          <div className="min-w-0 space-y-1">
            <CardTitle className="truncate text-base">
              <button
                type="button"
                className="text-left hover:underline"
                onClick={() => router.push(`/dashboard/workspaces/${workspace.id}`)}
                disabled={isOptimistic}
              >
                {workspace.name}
              </button>
            </CardTitle>
            {workspace.description && (
              <CardDescription className="line-clamp-2">{workspace.description}</CardDescription>
            )}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" disabled={isOptimistic}>
                <MoreHorizontal className="size-4" />
                <span className="sr-only">Actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                variant="destructive"
                onClick={() => setConfirmOpen(true)}
              >
                <Trash2 className="size-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            size="sm"
            className="w-full sm:w-auto"
            onClick={() => router.push(`/dashboard/workspaces/${workspace.id}`)}
            disabled={isOptimistic}
          >
            Open workspace
          </Button>
        </CardContent>
      </Card>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete workspace?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &quot;{workspace.name}&quot; and all related campaigns and knowledge bases.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting…' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

export function WorkspacesPage() {
  const client = useApiClient()
  const api = createResourceApi(client)

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: queryKeys.workspaces,
    queryFn: () => api.listWorkspaces(),
  })

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          title="Workspaces"
          description="Manage your campaign workspaces."
          actions={<WorkspaceCreateDialog />}
        />

        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-36 rounded-lg" />
            ))}
          </div>
        )}

        {isError && (
          <EmptyState
            title="Could not load workspaces"
            description={error instanceof Error ? error.message : 'Something went wrong'}
            action={
              <Button variant="outline" onClick={() => refetch()}>
                Try again
              </Button>
            }
          />
        )}

        {!isLoading && !isError && data?.items.length === 0 && (
          <EmptyState
            title="No workspaces yet"
            description="Create your first workspace to start managing campaigns."
            action={<WorkspaceCreateDialog />}
          />
        )}

        {!isLoading && !isError && data && data.items.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {data.items.map((workspace) => (
              <WorkspaceCard key={workspace.id} workspace={workspace} />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
