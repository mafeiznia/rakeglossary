/**
 * React Query hook for app metadata.
 *
 * staleTime: Infinity because version, author, and tech stack never change
 * during a session.
 */
import { useQuery } from '@tanstack/react-query'
import { fetchAbout } from '@/api/about'
import type { AboutResponse } from '@/types/about'

export function useAbout() {
  return useQuery<AboutResponse>({
    queryKey: ['about'],
    queryFn: fetchAbout,
    staleTime: Infinity,
  })
}