import { useState } from 'react';
import { useStore } from '../../store/app';

const LS_KEY = 'moa:prompt_templates';

function loadTemplates(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY) ?? '{}');
  } catch {
    return {};
  }
}

function saveTemplate(name: string, content: string) {
  const existing = loadTemplates();
  localStorage.setItem(LS_KEY, JSON.stringify({ ...existing, [name]: content }));
}

function deleteTemplate(name: string) {
  const existing = loadTemplates();
  delete existing[name];
  localStorage.setItem(LS_KEY, JSON.stringify(existing));
}

// ── Selected specialist row with expandable system prompt editor ─────────────

function SelectedSpecialistCard({
  model, provider, systemPrompt,
}: {
  model: string;
  provider: string;
  systemPrompt: string;
}) {
  const { toggleSpecialist, updateSpecialistPrompt } = useStore();
  const [expanded, setExpanded] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templates, setTemplates] = useState<Record<string, string>>(loadTemplates);
  const [saveMsg, setSaveMsg] = useState('');

  const refreshTemplates = () => setTemplates(loadTemplates());

  const handleSave = () => {
    const name = templateName.trim();
    if (!name) return;
    saveTemplate(name, systemPrompt);
    setTemplateName('');
    setSaveMsg('Saved!');
    setTimeout(() => setSaveMsg(''), 1500);
    refreshTemplates();
  };

  const handleDelete = (name: string) => {
    deleteTemplate(name);
    refreshTemplates();
  };

  const templateNames = Object.keys(templates);

  return (
    <div style={{
      marginBottom: 2,
      border: expanded ? '1px solid var(--border-mid)' : '1px solid transparent',
      background: 'rgba(212,247,1,0.03)',
    }}>
      {/* Row header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '9px 12px',
        borderLeft: '2px solid var(--accent)',
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700,
          color: 'var(--text)', letterSpacing: '0.05em', flex: 1, textTransform: 'uppercase',
        }}>
          {model}
        </span>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)',
          background: 'var(--bg-header)', padding: '2px 5px', letterSpacing: '0.06em',
        }}>
          {provider === 'ollama' ? 'LOCAL' : 'CLOUD'}
        </span>
        {/* System prompt toggle */}
        <button
          onClick={() => setExpanded((v) => !v)}
          title="Toggle system prompt editor"
          style={{
            background: 'transparent', border: '1px solid var(--border-mid)',
            color: 'var(--text-dim)', fontFamily: 'var(--font-mono)',
            fontSize: 9, padding: '3px 8px', cursor: 'pointer', letterSpacing: '0.06em',
            display: 'flex', alignItems: 'center', gap: 4,
          }}
        >
          PROMPT {expanded ? '▲' : '▼'}
        </button>
        {/* Remove */}
        <button
          onClick={() => toggleSpecialist({ model, provider, system_prompt: systemPrompt, temperature: 0.7, max_tokens: 1024 })}
          title="Remove specialist"
          style={{
            background: 'transparent', border: 'none',
            color: 'var(--text-dim)', fontSize: 14, cursor: 'pointer',
            lineHeight: 1, padding: '0 4px',
          }}
        >
          ×
        </button>
      </div>

      {/* Expandable prompt editor */}
      {expanded && (
        <div style={{ padding: '12px', borderTop: '1px solid var(--border)' }}>
          {/* Template selector */}
          {templateNames.length > 0 && (
            <div style={{ marginBottom: 8, display: 'flex', gap: 6, alignItems: 'center' }}>
              <select
                defaultValue=""
                onChange={(e) => {
                  if (e.target.value) {
                    updateSpecialistPrompt(model, provider, templates[e.target.value]);
                    e.target.value = '';
                  }
                }}
                style={{
                  flex: 1, background: 'var(--bg-header)', border: '1px solid var(--border-mid)',
                  color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 10,
                  padding: '4px 8px', cursor: 'pointer',
                }}
              >
                <option value="" disabled>Load template…</option>
                {templateNames.map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
              {/* Delete selected template button is per-template in a separate row below */}
            </div>
          )}

          {/* Saved templates list with delete */}
          {templateNames.length > 0 && (
            <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {templateNames.map((n) => (
                <span key={n} style={{
                  fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)',
                  background: 'var(--bg-header)', border: '1px solid var(--border)',
                  padding: '2px 6px', display: 'inline-flex', alignItems: 'center', gap: 4,
                }}>
                  {n}
                  <button onClick={() => handleDelete(n)} style={{
                    background: 'none', border: 'none', color: '#ef4444',
                    fontSize: 11, cursor: 'pointer', padding: 0, lineHeight: 1,
                  }}>×</button>
                </span>
              ))}
            </div>
          )}

          {/* Textarea */}
          <textarea
            value={systemPrompt}
            onChange={(e) => updateSpecialistPrompt(model, provider, e.target.value)}
            rows={5}
            style={{
              width: '100%', background: 'var(--bg-header)',
              border: '1px solid var(--border-mid)', color: 'var(--text)',
              fontFamily: 'var(--font-mono)', fontSize: 11, lineHeight: 1.5,
              padding: '8px 10px', resize: 'vertical', display: 'block',
            }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--accent)')}
            onBlur={(e) => (e.target.style.borderColor = 'var(--border-mid)')}
          />

          {/* Save as template */}
          <div style={{ marginTop: 8, display: 'flex', gap: 6, alignItems: 'center' }}>
            <input
              type="text"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              placeholder="Template name..."
              style={{
                flex: 1, background: 'var(--bg-header)', border: 'none',
                borderBottom: '1px solid var(--border-mid)', color: 'var(--text)',
                fontFamily: 'var(--font-mono)', fontSize: 10, padding: '4px 0',
              }}
              onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            />
            <button onClick={handleSave} disabled={!templateName.trim()} style={{
              background: 'transparent', border: '1px solid var(--border-mid)',
              color: saveMsg ? 'var(--accent)' : 'var(--text-dim)',
              fontFamily: 'var(--font-mono)', fontSize: 9, padding: '4px 10px',
              cursor: 'pointer', letterSpacing: '0.06em', flexShrink: 0,
            }}>
              {saveMsg || 'SAVE TEMPLATE'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Unselected model row ─────────────────────────────────────────────────────

function ModelRow({ model, provider, onToggle }: {
  model: string;
  provider: string;
  onToggle: () => void;
}) {
  return (
    <div
      onClick={onToggle}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 12px', background: 'transparent',
        borderLeft: '2px solid transparent', cursor: 'pointer', marginBottom: 2,
      }}
    >
      <div style={{
        width: 14, height: 14, border: '1px solid var(--border-mid)', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }} />
      <span style={{
        fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600,
        color: 'var(--text-mid)', letterSpacing: '0.05em', flex: 1, textTransform: 'uppercase',
      }}>
        {model}
      </span>
      <span style={{
        fontFamily: 'var(--font-mono)', fontSize: 9,
        color: provider === 'ollama' ? 'var(--text-dim)' : 'var(--accent-border)',
        background: 'var(--bg-header)', padding: '2px 5px', letterSpacing: '0.06em',
      }}>
        {provider === 'ollama' ? 'LOCAL' : 'CLOUD'}
      </span>
    </div>
  );
}

// ── Cloud model presets ──────────────────────────────────────────────────────

const CLOUD_MODELS: Record<string, string[]> = {
  openrouter: [
    'meta-llama/llama-3.1-70b-instruct',
    'anthropic/claude-3-haiku',
    'google/gemini-flash-1.5',
    'mistralai/mistral-7b-instruct',
  ],
  bytez: [
    'meta-llama/Llama-3.2-3B-Instruct',
    'Qwen/Qwen2.5-7B-Instruct',
  ],
};

// ── Main export ──────────────────────────────────────────────────────────────

export default function SpecialistPicker() {
  const { activeProvider, ollamaModels, selectedSpecialists, toggleSpecialist } = useStore();

  const models = activeProvider === 'ollama'
    ? ollamaModels.length > 0 ? ollamaModels : ['No Ollama models found']
    : CLOUD_MODELS[activeProvider] ?? [];

  return (
    <div>
      {/* Selected specialists with editors (shown at top) */}
      {selectedSpecialists
        .filter((s) => s.provider === activeProvider)
        .map((s) => (
          <SelectedSpecialistCard
            key={`${s.provider}:${s.model}`}
            model={s.model}
            provider={s.provider}
            systemPrompt={s.system_prompt ?? 'You are a helpful assistant.'}
          />
        ))}

      {/* Divider if any selected */}
      {selectedSpecialists.some((s) => s.provider === activeProvider) && (
        <div style={{
          fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)',
          letterSpacing: '0.1em', padding: '6px 12px 4px',
        }}>ADD MORE</div>
      )}

      {/* Unselected models */}
      {models.map((model) => {
        const isDisabled = model === 'No Ollama models found';
        const isSelected = !isDisabled && selectedSpecialists.some(
          (s) => s.model === model && s.provider === activeProvider,
        );
        if (isSelected) return null;
        return (
          <ModelRow
            key={model}
            model={model}
            provider={activeProvider}
            onToggle={() => {
              if (!isDisabled) {
                toggleSpecialist({
                  model,
                  provider: activeProvider,
                  system_prompt: 'You are a helpful assistant.',
                  temperature: 0.7,
                  max_tokens: 1024,
                });
              }
            }}
          />
        );
      })}
    </div>
  );
}
