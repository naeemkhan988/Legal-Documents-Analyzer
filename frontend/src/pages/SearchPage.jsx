import React, { useState } from 'react';
import SearchBar from '../components/Search/SearchBar';
import SearchResults from '../components/Search/SearchResults';
import { searchDocuments, ragAnswer } from '../services/searchService';
import { toast } from 'react-hot-toast';
import { MessageSquare, Search } from 'lucide-react';

export default function SearchPage() {
  const [results, setResults] = useState([]);
  const [answer, setAnswer] = useState(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('search'); // 'search' | 'rag'

  const handleSearch = async (q) => {
    setQuery(q);
    setLoading(true);
    try {
      if (mode === 'rag') {
        const data = await ragAnswer(q);
        setAnswer(data.answer);
        setResults(data.sources || []);
      } else {
        const data = await searchDocuments(q);
        setResults(data.results || []);
        setAnswer(null);
      }
    } catch (err) { toast.error(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold gradient-text">Semantic Search</h1>

      {/* Mode Toggle */}
      <div className="flex gap-2">
        <button onClick={() => setMode('search')} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm transition ${mode === 'search' ? 'bg-brand-600/20 text-brand-400' : 'text-surface-300 hover:bg-surface-800'}`}>
          <Search size={16} /> Search
        </button>
        <button onClick={() => setMode('rag')} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm transition ${mode === 'rag' ? 'bg-brand-600/20 text-brand-400' : 'text-surface-300 hover:bg-surface-800'}`}>
          <MessageSquare size={16} /> Ask AI (RAG)
        </button>
      </div>

      <SearchBar onSearch={handleSearch} loading={loading} placeholder={mode === 'rag' ? 'Ask a question about your contracts…' : 'Search across all documents…'} />

      {/* RAG Answer */}
      {answer && (
        <div className="glass-card animate-slide-up">
          <h3 className="text-sm font-semibold text-brand-400 mb-2">AI Answer</h3>
          <p className="text-sm text-surface-200 whitespace-pre-wrap">{answer}</p>
        </div>
      )}

      <SearchResults results={results} query={query} />
    </div>
  );
}
