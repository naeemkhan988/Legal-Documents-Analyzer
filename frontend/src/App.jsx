import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { DocumentProvider } from './context/DocumentContext';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import Footer from './components/Layout/Footer';
import Dashboard from './pages/Dashboard';
import DocumentPage from './pages/DocumentPage';
import AnalysisPage from './pages/AnalysisPage';
import SearchPage from './pages/SearchPage';
import ComparePage from './pages/ComparePage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';
import NotFoundPage from './pages/NotFoundPage';

export default function App() {
  return (
    <AppProvider>
      <DocumentProvider>
        <div className="min-h-screen flex flex-col">
          <Header />
          <div className="flex flex-1">
            <Sidebar />
            <main className="flex-1 p-4 md:p-6 overflow-y-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/document/:id" element={<DocumentPage />} />
                <Route path="/analysis/:id" element={<AnalysisPage />} />
                <Route path="/search" element={<SearchPage />} />
                <Route path="/compare" element={<ComparePage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </main>
          </div>
          <Footer />
        </div>
      </DocumentProvider>
    </AppProvider>
  );
}
