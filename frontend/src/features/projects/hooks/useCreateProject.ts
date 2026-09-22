import { useMutation } from '@tanstack/react-query'
import { projectsApi, sourcesApi, processApi } from '@/api'
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
  const trimmedTitle = title.trim()
  if (!trimmedTitle) {
    throw new Error('Title is required')
  }
  if (!file && !(text && text.trim())) {
    throw new Error('No source provided')
  }

  // 1) Create the project shell
  const project = await projectsApi.createEmpty({ title: trimmedTitle })

  // 2) Attach the source
  if (file) {
    await sourcesApi.uploadFiles(project.id, [file])
  } else if (text) {
    await sourcesApi.addText(project.id, {
      name: trimmedTitle,
      text: text.trim(),
    })
  }

  // 3) Kick off processing with all options
  const started = await processApi.start(project.id, options)
  return { project: started }
}

export function useCreateProject() {
  return useMutation({
    mutationFn: createProject,
  })
}