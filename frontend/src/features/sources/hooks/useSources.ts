import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { sourcesApi } from '@/api'
import type {
  ProjectSourceUpdate,
  TextSourceCreate,
} from '@/types'

export function useSources(projectId: string | undefined) {
  const qc = useQueryClient()

  const query = useQuery({
    queryKey: ['sources', projectId],
    queryFn: () => sourcesApi.list(projectId!),
    enabled: !!projectId,
  })

  const invalidateAll = () => {
    qc.invalidateQueries({ queryKey: ['sources', projectId] })
    qc.invalidateQueries({ queryKey: ['project', projectId] })
    qc.invalidateQueries({ queryKey: ['projects'] })
  }

  const uploadMutation = useMutation({
    mutationFn: (files: File[]) => sourcesApi.uploadFiles(projectId!, files),
    onSuccess: invalidateAll,
  })

  const addTextMutation = useMutation({
    mutationFn: (payload: TextSourceCreate) =>
      sourcesApi.addText(projectId!, payload),
    onSuccess: invalidateAll,
  })

  const updateMutation = useMutation({
    mutationFn: ({
      sourceId,
      payload,
    }: {
      sourceId: number
      payload: ProjectSourceUpdate
    }) => sourcesApi.update(projectId!, sourceId, payload),
    onSuccess: invalidateAll,
  })

  const removeMutation = useMutation({
    mutationFn: (sourceId: number) => sourcesApi.remove(projectId!, sourceId),
    onSuccess: invalidateAll,
  })

  return {
    sources: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    upload: uploadMutation.mutateAsync,
    addText: addTextMutation.mutateAsync,
    update: updateMutation.mutateAsync,
    remove: removeMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    isAddingText: addTextMutation.isPending,
    isUpdating: updateMutation.isPending,
    isRemoving: removeMutation.isPending,
  }
}