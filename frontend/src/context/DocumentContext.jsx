import { createContext, useContext, useState, useCallback } from 'react';

const DocumentContext = createContext(null);

export function DocumentProvider({ children }) {
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [documents, setDocuments] = useState([]);

  const addDocument = useCallback((doc) => {
    setDocuments((prev) => [doc, ...prev]);
  }, []);

  return (
    <DocumentContext.Provider value={{ selectedDocument, setSelectedDocument, documents, setDocuments, addDocument }}>
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocumentContext() {
  const ctx = useContext(DocumentContext);
  if (!ctx) throw new Error('useDocumentContext must be used within DocumentProvider');
  return ctx;
}
