import { useMutation } from '@tanstack/react-query'
import { projectsApi, processApi } from '@/api'
import type { ProcessRequest, ProjectRead } from '@/types'

interface CreateParams {
  title: string
  file?: File | null
  text?: string | null
  options: ProcessRequest
}

interface CreateResult {
  project: ProjectRead
}

async function createProject({
  title,
  file,
  text,
  options,
}: CreateParams): Promise<CreateResult> {
  let project: ProjectRead

  if (file) {
    project = await projectsApi.createFromUpload(file, title)
  } else if (text && text.trim()) {
    project = await projectsApi.createFromText({ title, text })
  } else {
    throw new Error('No source provided')
  }

  // Immediately start processing
  const started = await processApi.start(project.id, options)
  return { project: started }
}

export function useCreateProject() {
  return useMutation({
    mutationFn: createProject,
  })
}