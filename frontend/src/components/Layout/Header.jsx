import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, Scale, Search, Bell } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';

export default function Header() {
  const { sidebarOpen, setSidebarOpen } = useAppContext();
  const location = useLocation();

  const pageTitle = {
    '/':          'Dashboard',
    '/search':    'Semantic Search',
    '/compare':   'Compare Contracts',
    '/reports':   'Reports',
    '/settings':  'Settings',
  }[location.pathname] || 'Document';

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 border-b border-white/5 bg-surface-950/80 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden p-2 rounded-lg hover:bg-surface-800 transition">
          <Menu size={20} />
        </button>
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
            <Scale size={16} className="text-white" />
          </div>
          <span className="text-lg font-bold gradient-text hidden sm:inline">LegalRAG</span>
        </Link>
      </div>

      <h1 className="text-sm font-medium text-surface-300 hidden md:block">{pageTitle}</h1>

      <div className="flex items-center gap-3">
        <Link to="/search" className="p-2 rounded-lg hover:bg-surface-800 transition text-surface-300 hover:text-white">
          <Search size={18} />
        </Link>
        <button className="p-2 rounded-lg hover:bg-surface-800 transition text-surface-300 hover:text-white relative">
          <Bell size={18} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-brand-500 rounded-full" />
        </button>
        <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold">U</div>
      </div>
    </header>
  );
}
