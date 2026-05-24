import React from 'react';

export default function Footer() {
  return (
    <footer className="border-t border-white/5 py-4 px-6 text-center text-xs text-surface-300/60">
      <p>© {new Date().getFullYear()} LegalRAG — AI-Powered Legal Document Analyzer. All rights reserved.</p>
    </footer>
  );
}
