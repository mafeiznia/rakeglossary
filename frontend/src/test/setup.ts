/**
 * Vitest global setup.
 *
 * - Loads jest-dom matchers (toBeInTheDocument, toHaveTextContent, ...)
 * - Cleans up the DOM after each test
 */
import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})