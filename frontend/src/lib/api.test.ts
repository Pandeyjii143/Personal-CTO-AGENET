// Runtime validation coverage for: prompt-driven generation API requests
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from './api'

describe('apiRequest', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sends the generation prompt and returns the created run', async () => {
    const run = { id: 7, status: 'queued' }
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify(run), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(apiRequest('/generation-runs', {
      method: 'POST',
      body: JSON.stringify({ prompt: 'Build a personal task tracker' }),
    })).resolves.toEqual(run)

    expect(fetch).toHaveBeenCalledWith('/api/generation-runs', {
      method: 'POST',
      body: JSON.stringify({ prompt: 'Build a personal task tracker' }),
      headers: { 'Content-Type': 'application/json' },
    })
  })

  it('sends an optional OpenAI key only in the request header', async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ id: 8, status: 'queued' }), {
        status: 202,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await apiRequest('/generation-runs', {
      method: 'POST',
      body: JSON.stringify({ prompt: 'Build a personal task tracker' }),
      headers: { 'X-OpenAI-API-Key': 'test-key' },
    })

    expect(fetch).toHaveBeenCalledWith('/api/generation-runs', {
      method: 'POST',
      body: JSON.stringify({ prompt: 'Build a personal task tracker' }),
      headers: {
        'Content-Type': 'application/json',
        'X-OpenAI-API-Key': 'test-key',
      },
    })
  })

  it('surfaces the backend error detail and HTTP status', async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Generation service unavailable' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(apiRequest('/generation-runs')).rejects.toMatchObject({
      name: 'ApiError',
      message: 'Generation service unavailable',
      status: 503,
    })
  })
})
