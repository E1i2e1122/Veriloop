import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('ai', async (importOriginal) => ({
  ...(await importOriginal<typeof import('ai')>()),
  generateObject: vi.fn(),
}));

vi.mock('./backend-client', () => ({
  backendFetch: vi.fn(),
}));

import { generateObject } from 'ai';
import { routeAssistantIntent } from './intent-router';

const generateObjectMock = vi.mocked(generateObject);

function context(modelId: string, text = 'Start AutoPilot on https://example.com') {
  return {
    messages: [{ role: 'user', parts: [{ type: 'text', text }] }],
    model: { specificationVersion: 'v3', provider: 'anthropic.messages', modelId } as any,
  };
}

describe('routeAssistantIntent', () => {
  beforeEach(() => {
    generateObjectMock.mockReset();
  });

  it('uses native JSON output without temperature on models that reject forced tool calls', async () => {
    generateObjectMock.mockResolvedValue({
      object: {
        intent: 'startAutoPilot',
        confidence: 1.4,
        input: '{"url":"https://example.com"}',
        missingFields: [],
        reason: 'explicit start request',
      },
    } as any);

    const route = await routeAssistantIntent(context('claude-sonnet-5-5'));

    const request = generateObjectMock.mock.calls[0][0] as any;
    expect(request).not.toHaveProperty('temperature');
    expect(request.providerOptions).toEqual({ anthropic: { structuredOutputMode: 'outputFormat', effort: 'low' } });
    expect(route).toMatchObject({
      kind: 'action',
      toolName: 'startAutoPilot',
      confidence: 1,
      input: { urls: ['https://example.com/'] },
    });
  });

  it('treats unparseable native input as empty and asks for the missing URL', async () => {
    generateObjectMock.mockResolvedValue({
      object: { intent: 'startAutoPilot', confidence: 0.9, input: 'not json', missingFields: [], reason: '' },
    } as any);

    const route = await routeAssistantIntent(context('claude-opus-5-5', 'Start AutoPilot please'));

    expect(route).toMatchObject({ kind: 'clarify', intent: 'startAutoPilot', missingFields: ['url'] });
  });

  it('keeps the generateObject defaults for other models', async () => {
    generateObjectMock.mockResolvedValue({
      object: {
        intent: 'startAutoPilot',
        confidence: 0.9,
        input: { url: 'https://example.com' },
        missingFields: [],
        reason: '',
      },
    } as any);

    const route = await routeAssistantIntent(context('glm-5.1'));

    const request = generateObjectMock.mock.calls[0][0] as any;
    expect(request.temperature).toBe(0);
    expect(request).not.toHaveProperty('providerOptions');
    expect(route).toMatchObject({ kind: 'action', toolName: 'startAutoPilot', input: { urls: ['https://example.com/'] } });
  });

  it('returns null when the model call fails', async () => {
    generateObjectMock.mockRejectedValue(new Error('provider error'));
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});

    await expect(routeAssistantIntent(context('claude-sonnet-5-5'))).resolves.toBeNull();
    warn.mockRestore();
  });
});
