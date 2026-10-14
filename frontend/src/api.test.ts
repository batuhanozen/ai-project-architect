import { getHealth } from './api'

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

test.each([null, {}, { status: 'broken' }])('rejects an invalid health payload: %j', async (data) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => data }))
  await expect(getHealth('live')).rejects.toThrow('Invalid health response')
})

test('does not expose malformed response content', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => { throw new SyntaxError('private response content') },
  }))
  await expect(getHealth('live')).rejects.toThrow('Invalid health response')
})

test('aborts a health request after five seconds', async () => {
  vi.useFakeTimers()
  vi.stubGlobal('fetch', vi.fn((_url: string, options: RequestInit) => new Promise((_resolve, reject) => {
    options.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
  })))
  const result = expect(getHealth('ready')).rejects.toThrow('Health check timed out')
  await vi.advanceTimersByTimeAsync(5000)
  await result
})
