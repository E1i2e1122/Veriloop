/**
 * Request options that newer Claude models handle differently from older ones.
 *
 * Keep NO_SAMPLING_CLAUDE_PREFIXES in sync with _NO_SAMPLING_CLAUDE_PREFIXES in
 * orchestrator/services/ai_runtime_config.py.
 */

// These models return a 400 for temperature, top_p and top_k.
const NO_SAMPLING_CLAUDE_PREFIXES = [
  'claude-opus-4-7',
  'claude-opus-4-8',
  'claude-opus-5',
  'claude-sonnet-5',
  'claude-haiku-5',
  'claude-fable',
  'claude-mythos',
];

// Claude models with native JSON outputs that @ai-sdk/anthropic 3.0.x does not recognise.
// For models it does not know, generateObject falls back to a forced "json" tool call,
// which Claude Opus 5.5, Claude Sonnet 5.5 and Claude Fable/Mythos 5.1+ reject with a 400.
const NATIVE_STRUCTURED_OUTPUT_PREFIXES = [
  'claude-opus-4-8',
  'claude-opus-5',
  'claude-sonnet-5',
  'claude-haiku-5',
  'claude-fable',
  'claude-mythos',
];

function modelName(modelId?: string | null): string {
  return (modelId || '').trim().toLowerCase().split('/').pop() || '';
}

export function acceptsSamplingParams(modelId?: string | null): boolean {
  const name = modelName(modelId);
  return !NO_SAMPLING_CLAUDE_PREFIXES.some((prefix) => name.startsWith(prefix));
}

export function supportsNativeStructuredOutput(modelId?: string | null): boolean {
  const name = modelName(modelId);
  return NATIVE_STRUCTURED_OUTPUT_PREFIXES.some((prefix) => name.startsWith(prefix));
}
