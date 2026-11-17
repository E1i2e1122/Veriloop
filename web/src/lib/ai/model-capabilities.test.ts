import { describe, expect, it } from 'vitest';
import { acceptsSamplingParams, supportsNativeStructuredOutput } from './model-capabilities';

describe('acceptsSamplingParams', () => {
  it.each([
    'claude-sonnet-5-5',
    'claude-opus-5-5',
    'claude-haiku-5-5',
    'claude-opus-4-8',
    'claude-opus-4-7',
    'claude-fable-5-2',
    'anthropic/claude-sonnet-5-5',
    ' Claude-Sonnet-5-5 ',
  ])('is false for %s', (modelId) => {
    expect(acceptsSamplingParams(modelId)).toBe(false);
  });

  it.each(['claude-sonnet-4-5', 'claude-opus-4-6', 'claude-haiku-4-5-20251001', 'glm-5.1', 'gpt-5', '', undefined, null])(
    'is true for %s',
    (modelId) => {
      expect(acceptsSamplingParams(modelId)).toBe(true);
    }
  );
});

describe('supportsNativeStructuredOutput', () => {
  it.each(['claude-sonnet-5-5', 'claude-opus-5-5', 'claude-haiku-5-5', 'claude-opus-4-8', 'claude-fable-5-2', 'anthropic/claude-opus-5-5'])(
    'is true for %s',
    (modelId) => {
      expect(supportsNativeStructuredOutput(modelId)).toBe(true);
    }
  );

  it.each(['claude-sonnet-4-5', 'claude-opus-4-7', 'glm-5.1', 'gpt-5', '', undefined])('is false for %s', (modelId) => {
    expect(supportsNativeStructuredOutput(modelId)).toBe(false);
  });
});
