'use client'

import { useQuery } from '@tanstack/react-query'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { useApiClient } from '@/hooks/use-api-client'
import { createResourceApi, queryKeys } from '@/lib/api-resources'
import type { CampaignAnalyticsResponse } from '@/lib/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/page-header'

export function CampaignAnalyticsPanel({
  workspaceId,
  campaignId,
  enabled,
}: {
  workspaceId: string
  campaignId: string
  enabled: boolean
}) {
  const client = useApiClient()
  const api = createResourceApi(client)

  const analyticsQuery = useQuery({
    queryKey: [...queryKeys.campaign(workspaceId, campaignId), 'analytics'],
    queryFn: () => api.getCampaignAnalytics(workspaceId, campaignId),
    enabled,
    refetchInterval: enabled ? 30000 : false,
  })

  if (!enabled) {
    return (
      <EmptyState
        title="Analytics not available yet"
        description="Publish at least one content piece to see performance metrics."
      />
    )
  }

  if (analyticsQuery.isLoading) {
    return <Skeleton className="h-64 w-full" />
  }

  const data = analyticsQuery.data
  if (!data) {
    return (
      <EmptyState
        title="No analytics data"
        description="Metrics will appear after the analytics poll task runs."
      />
    )
  }

  const chartData = data.by_platform.map((row) => ({
    platform: row.platform,
    impressions: row.impressions,
    engagements: row.engagements,
  }))

  const hasMetrics = data.totals.impressions > 0

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Impressions" value={data.totals.impressions} />
        <MetricCard label="Engagements" value={data.totals.engagements} />
        <MetricCard label="Engagement rate" value={`${(data.totals.engagement_rate * 100).toFixed(1)}%`} />
        <MetricCard label="CTR" value={`${(data.totals.ctr * 100).toFixed(2)}%`} />
      </div>

      {!hasMetrics && (
        <p className="text-sm text-muted-foreground">
          Metrics pending — analytics poll runs shortly after publish.
        </p>
      )}

      {chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Impressions by platform</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="platform" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="impressions" fill="hsl(var(--primary))" name="Impressions" />
                <Bar dataKey="engagements" fill="hsl(var(--chart-2, 220 70% 50%))" name="Engagements" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {data.variants.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">A/B variant comparison</CardTitle>
            <CardDescription>Engagement rate by variant per platform</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Platform</th>
                    <th className="pb-2 pr-4">Variant A</th>
                    <th className="pb-2 pr-4">Variant B</th>
                    <th className="pb-2">Winner</th>
                  </tr>
                </thead>
                <tbody>
                  {data.variants.map((row) => (
                    <tr key={row.platform} className="border-b last:border-0">
                      <td className="py-2 pr-4 capitalize">{row.platform}</td>
                      <td className="py-2 pr-4">{(row.variant_a_rate * 100).toFixed(2)}%</td>
                      <td className="py-2 pr-4">{(row.variant_b_rate * 100).toFixed(2)}%</td>
                      <td className="py-2 font-medium">Variant {row.winner}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Content performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-4">Platform</th>
                  <th className="pb-2 pr-4">Variant</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2 pr-4">Impressions</th>
                  <th className="pb-2">Eng. rate</th>
                </tr>
              </thead>
              <tbody>
                {data.contents.map((row) => (
                  <tr key={row.content_id} className="border-b last:border-0">
                    <td className="py-2 pr-4 capitalize">{row.platform}</td>
                    <td className="py-2 pr-4">{row.variant}</td>
                    <td className="py-2 pr-4 capitalize">{row.status}</td>
                    <td className="py-2 pr-4">{row.engagement_metrics.impressions ?? '—'}</td>
                    <td className="py-2">
                      {row.engagement_metrics.engagement_rate != null
                        ? `${(row.engagement_metrics.engagement_rate * 100).toFixed(2)}%`
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  )
}
