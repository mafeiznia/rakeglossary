import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { projectsApi, processApi } from '@/api'
import type { ProcessRequest } from '@/types'

export function useProject(projectId: string | undefined) {
  const qc = useQueryClient()

  const query = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
    refetchInterval: (q) => {
      const s = q.state.data?.status
      return s === 'pending' || s === 'processing' ? 1500 : false
    },
  })

  const prevStatus = useRef<string | undefined>(undefined)
  useEffect(() => {
    const current = query.data?.status
    if (!projectId || !current) return
    const prev = prevStatus.current
    if (
      prev !== undefined &&
      prev !== 'done' &&
      prev !== 'failed' &&
      prev !== 'cancelled' &&
      (current === 'done' || current === 'failed' || current === 'cancelled')
    ) {
      qc.invalidateQueries({ queryKey: ['glossary', projectId] })
    }
    prevStatus.current = current
  }, [query.data?.status, projectId, qc])

  const reprocessMutation = useMutation({
    mutationFn: (options: ProcessRequest) => processApi.start(projectId!, options),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  const cancelMutation = useMutation({
    mutationFn: () => processApi.cancel(projectId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  return {
    ...query,
    reprocess: reprocessMutation.mutateAsync,
    cancel: cancelMutation.mutateAsync,
    isReprocessing: reprocessMutation.isPending,
    isCancelling: cancelMutation.isPending,
  }
}