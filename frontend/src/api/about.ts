/**
 * API client for app metadata (/api/about).
 *
 * Uses the shared axios instance from ./client.
 * Backend: GET /api/about (see backend/app/api/meta.py).
 */
import { api } from './client';
import type { AboutResponse } from '@/types/about';

/**
 * Fetch application metadata: version, author, tech stack, etc.
 * Cached by TanStack Query (staleTime: Infinity) since it never changes at runtime.
 */
export async function fetchAbout(): Promise<AboutResponse> {
  const response = await api.get<AboutResponse>('/about');
  return response.data;
}