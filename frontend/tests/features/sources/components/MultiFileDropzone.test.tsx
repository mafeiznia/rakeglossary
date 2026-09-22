/**
 * Tests for MultiFileDropzone — render only.
 *
 * React-dropzone's drag interaction is not exercised; we only verify that
 * the visual surface renders correctly and respects the `disabled` prop.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

import { MultiFileDropzone } from '@/features/sources/components/MultiFileDropzone'

describe('MultiFileDropzone', () => {
  it('renders title and hint', () => {
    render(<MultiFileDropzone onFiles={vi.fn()} />)
    expect(screen.getByText('sources.dropzoneTitle')).toBeInTheDocument()
    expect(screen.getByText('sources.dropzoneHint')).toBeInTheDocument()
  })

  it('renders a hidden file input', () => {
    const { container } = render(<MultiFileDropzone onFiles={vi.fn()} />)
    expect(container.querySelector('input[type="file"]')).toBeInTheDocument()
  })

  it('applies reduced opacity when disabled', () => {
    const { container } = render(
      <MultiFileDropzone onFiles={vi.fn()} disabled />
    )
    const root = container.firstChild as HTMLElement
    expect(root.style.opacity).toBe('0.5')
    expect(root.style.cursor).toBe('not-allowed')
  })
})