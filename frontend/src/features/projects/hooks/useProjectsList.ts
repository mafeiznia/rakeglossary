import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '@/api'

export function useProjectsList(page = 1, pageSize = 50) {
  const qc = useQueryClient()

  const query = useQuery({
    queryKey: ['projects', page, pageSize],
    queryFn: () => projectsApi.list(page, pageSize),
    staleTime: 10_000,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  return {
    ...query,
    remove: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  }
}