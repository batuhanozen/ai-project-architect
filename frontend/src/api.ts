export type Health = { status: 'ok' }

const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '')

export async function getHealth(kind: 'live' | 'ready'): Promise<Health> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 5000)
  try {
    const response = await fetch(`${baseUrl}/health/${kind}`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
    if (!response.ok) {
      throw new Error(kind === 'ready' ? 'Database is unavailable' : 'API is unavailable')
    }
    let data: unknown
    try {
      data = await response.json()
    } catch {
      throw new Error('Invalid health response')
    }
    if (typeof data !== 'object' || data === null || !('status' in data) || data.status !== 'ok') {
      throw new Error('Invalid health response')
    }
    return { status: 'ok' }
  } catch (error) {
    if (controller.signal.aborted) throw new Error('Health check timed out')
    if (error instanceof TypeError) {
      throw new Error(kind === 'ready' ? 'Cannot reach API to check database' : 'Cannot reach API service')
    }
    throw error
  } finally {
    clearTimeout(timeout)
  }
}
