import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import App from './App'

afterEach(() => {
  vi.unstubAllGlobals()
})

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter><App /></MemoryRouter>
    </QueryClientProvider>,
  )
}

test('shows real API and database health', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'ok' }) }))
  renderApp()
  await waitFor(() => expect(screen.getAllByText('Operational')).toHaveLength(2))
  expect(screen.getByText('PostgreSQL is accepting queries.')).toBeTruthy()
})

test('shows a database error rather than false success', async () => {
  vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve({
    ok: !url.includes('/ready'),
    json: async () => ({ status: 'ok' }),
  })))
  renderApp()
  await waitFor(() => expect(screen.getByText('Database is unavailable')).toBeTruthy())
})

test('explains when the API cannot be reached', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  renderApp()
  await waitFor(() => expect(screen.getByText('Cannot reach API service')).toBeTruthy())
  expect(screen.getByText('Cannot reach API to check database')).toBeTruthy()
})
