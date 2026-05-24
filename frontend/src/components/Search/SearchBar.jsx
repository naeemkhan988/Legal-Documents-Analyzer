import React, { useState } from 'react';
import { Search } from 'lucide-react';
import Button from '../Common/Button';

export default function SearchBar({ onSearch, loading, placeholder = 'Ask a question about your documents…' }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) onSearch?.(query.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="glass-card !p-3 flex items-center gap-3">
      <Search size={18} className="text-surface-300 flex-shrink-0" />
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="flex-1 bg-transparent text-surface-100 placeholder-surface-300/50 focus:outline-none text-sm"
      />
      <Button type="submit" loading={loading} className="!py-2 !px-4 text-sm">Search</Button>
    </form>
  );
}
