import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { uploadDocument } from '../../services/documentService';
import Button from '../Common/Button';

const ACCEPTED = { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'], 'text/plain': ['.txt'] };
const MAX_SIZE = 50 * 1024 * 1024; // 50 MB

export default function DocumentUpload({ onUploadComplete }) {
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(null);

  const onDrop = useCallback(async (accepted, rejected) => {
    if (rejected.length) { toast.error('Invalid file type or size.'); return; }
    const file = accepted[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);
    setUploaded(null);

    try {
      const doc = await uploadDocument(file, setProgress);
      setUploaded(doc);
      toast.success(`"${doc.filename}" uploaded successfully!`);
      onUploadComplete?.(doc);
    } catch (err) {
      toast.error(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: ACCEPTED, maxSize: MAX_SIZE, multiple: false,
  });

  return (
    <div className="glass-card">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ${
          isDragActive ? 'border-brand-500 bg-brand-500/10' : 'border-surface-700 hover:border-brand-500/50'
        }`}
      >
        <input {...getInputProps()} />
        {uploaded ? (
          <div className="flex flex-col items-center gap-3 animate-fade-in">
            <CheckCircle size={40} className="text-green-400" />
            <p className="text-green-400 font-medium">{uploaded.filename}</p>
            <p className="text-surface-300 text-sm">Uploaded & processed successfully</p>
            <Button variant="secondary" onClick={(e) => { e.stopPropagation(); setUploaded(null); }}>Upload Another</Button>
          </div>
        ) : uploading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-brand-400 font-medium">Processing… {progress}%</p>
            <div className="w-48 h-2 bg-surface-800 rounded-full overflow-hidden">
              <div className="h-full bg-brand-500 rounded-full transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-2xl bg-brand-600/20 flex items-center justify-center">
              <Upload size={24} className="text-brand-400" />
            </div>
            <p className="text-surface-100 font-medium">{isDragActive ? 'Drop your file here' : 'Drag & drop a legal document'}</p>
            <p className="text-surface-300 text-sm">PDF, DOCX, or TXT — up to 50 MB</p>
          </div>
        )}
      </div>
    </div>
  );
}
