import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api'

const QUERY_KEY = ['stopwords']

export function useStopwords() {
  const qc = useQueryClient()

  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: settingsApi.getStopwords,
    staleTime: 60_000,
  })

  const addMutation = useMutation({
    mutationFn: (word: string) => settingsApi.addStopword(word),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })

  const removeMutation = useMutation({
    mutationFn: (word: string) => settingsApi.removeStopword(word),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })

  return {
    words: query.data?.words ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    add: addMutation.mutateAsync,
    remove: removeMutation.mutateAsync,
    isAdding: addMutation.isPending,
    isRemoving: removeMutation.isPending,
  }
}