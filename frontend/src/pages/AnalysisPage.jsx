import React from 'react';
import { useParams, Navigate } from 'react-router-dom';

// AnalysisPage is a redirect — analysis is shown within DocumentPage
export default function AnalysisPage() {
  const { id } = useParams();
  return <Navigate to={`/document/${id}`} replace />;
}
