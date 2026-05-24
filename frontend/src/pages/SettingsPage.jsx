import React from 'react';
import { Settings as SettingsIcon, Globe, Cpu, Database } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold gradient-text flex items-center gap-2"><SettingsIcon size={24} /> Settings</h1>

      <div className="glass-card">
        <h3 className="font-semibold mb-4">LLM Configuration</h3>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-surface-300 mb-1 block">Backend</label>
            <select className="input-field" defaultValue="ollama">
              <option value="ollama">Ollama (Local)</option>
              <option value="groq">Groq (Cloud)</option>
              <option value="huggingface">HuggingFace</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-surface-300 mb-1 block">Model</label>
            <input className="input-field" defaultValue="mistral" placeholder="e.g. mistral, llama2" />
          </div>
        </div>
      </div>

      <div className="glass-card">
        <h3 className="font-semibold mb-4">System Info</h3>
        <div className="space-y-2 text-sm text-surface-300">
          <p className="flex items-center gap-2"><Globe size={14} /> API: http://localhost:8000</p>
          <p className="flex items-center gap-2"><Database size={14} /> Database: SQLite</p>
          <p className="flex items-center gap-2"><Cpu size={14} /> Embeddings: all-MiniLM-L6-v2</p>
        </div>
      </div>
    </div>
  );
}
