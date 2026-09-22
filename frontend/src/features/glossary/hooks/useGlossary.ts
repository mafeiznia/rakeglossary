import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { glossaryApi } from '@/api'
import type { GlossaryEntryUpdate } from '@/types'

export function useGlossary(projectId: string | undefined) {
  const qc = useQueryClient()

  const query = useQuery({
    queryKey: ['glossary', projectId],
    queryFn: () => glossaryApi.list(projectId!),
    enabled: !!projectId,
  })

  const updateMutation = useMutation({
    mutationFn: ({
      entryId,
      payload,
    }: {
      entryId: number
      payload: GlossaryEntryUpdate
    }) => glossaryApi.update(entryId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['glossary', projectId] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (entryId: number) => glossaryApi.delete(entryId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['glossary', projectId] })
    },
  })

  return {
    ...query,
    update: updateMutation.mutateAsync,
    remove: deleteMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  }
}