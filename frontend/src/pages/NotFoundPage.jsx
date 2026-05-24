import React from 'react';
import { Link } from 'react-router-dom';
import { Home, AlertTriangle } from 'lucide-react';
import Button from '../components/Common/Button';

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center animate-fade-in">
      <AlertTriangle size={48} className="text-yellow-400 mb-4" />
      <h1 className="text-4xl font-bold mb-2">404</h1>
      <p className="text-surface-300 mb-6">The page you're looking for doesn't exist.</p>
      <Link to="/"><Button icon={Home}>Back to Dashboard</Button></Link>
    </div>
  );
}
