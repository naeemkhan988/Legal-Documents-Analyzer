import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Search, GitCompare, FileBarChart, Settings } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';

const NAV_ITEMS = [
  { to: '/',         icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/search',   icon: Search,          label: 'Search' },
  { to: '/compare',  icon: GitCompare,      label: 'Compare' },
  { to: '/reports',  icon: FileBarChart,    label: 'Reports' },
  { to: '/settings', icon: Settings,        label: 'Settings' },
];

export default function Sidebar() {
  const { sidebarOpen } = useAppContext();

  return (
    <aside className={`fixed lg:sticky top-16 left-0 z-20 h-[calc(100vh-4rem)] bg-surface-950 border-r border-white/5 transition-all duration-300 ${sidebarOpen ? 'w-56' : 'w-0 lg:w-16'} overflow-hidden`}>
      <nav className="flex flex-col gap-1 p-3 pt-4">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-brand-600/20 text-brand-400 shadow-inner'
                  : 'text-surface-300 hover:bg-surface-800 hover:text-white'
              }`
            }
          >
            <Icon size={18} className="flex-shrink-0" />
            <span className={`${sidebarOpen ? 'opacity-100' : 'lg:opacity-0 lg:w-0'} transition-opacity`}>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
