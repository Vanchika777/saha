import React, { useState } from 'react';
import { useBookStore } from '../store/bookStore';
import { api } from '../utils/api';
import { X, UploadCloud, FileText, Loader2 } from 'lucide-react';

export const UploadModal: React.FC = () => {
  const { isUploadModalOpen, closeUploadModal, addBook, toggleBookSelection } = useBookStore();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isUploadModalOpen) return null;

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      if (selected.type === 'application/pdf' || selected.name.endsWith('.pdf')) {
        setFile(selected);
        setError('');
      } else {
        setError('Only PDF files are allowed');
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/books/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      addBook(res.data.book);
      toggleBookSelection(res.data.book.id);
      closeUploadModal();
      setFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.error || 'Failed to upload PDF book');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="backdrop" onClick={closeUploadModal}>
      <div
        className="glass"
        style={{
          width: '100%',
          maxWidth: '460px',
          padding: '32px',
          position: 'relative',
          borderRadius: 'var(--radius-xl)',
          background: 'var(--color-surface)',
          boxShadow: 'var(--shadow-lg)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={closeUploadModal}
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            color: 'var(--color-text-muted)',
          }}
        >
          <X size={20} />
        </button>

        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h2 className="serif" style={{ fontSize: '1.5rem', marginBottom: '6px' }}>
            Upload Book PDF
          </h2>
          <p className="text-muted" style={{ fontSize: '0.85rem' }}>
            Saha will extract metadata, cover, and build RAG vectors automatically.
          </p>
        </div>

        {error && (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#ef4444',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
              marginBottom: '16px',
            }}
          >
            {error}
          </div>
        )}

        {/* Drop Zone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          style={{
            border: '2px dashed var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '32px 20px',
            textAlign: 'center',
            background: 'var(--color-surface-2)',
            cursor: 'pointer',
            marginBottom: '20px',
          }}
          onClick={() => document.getElementById('pdf-input')?.click()}
        >
          <input
            id="pdf-input"
            type="file"
            accept=".pdf"
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
          <UploadCloud size={40} color="var(--color-primary)" style={{ margin: '0 auto 12px' }} />
          {file ? (
            <div className="flex items-center justify-center gap-2" style={{ color: 'var(--color-success)' }}>
              <FileText size={18} />
              <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{file.name}</span>
            </div>
          ) : (
            <>
              <p style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '4px' }}>
                Drag and drop your PDF here
              </p>
              <p className="text-muted" style={{ fontSize: '0.78rem' }}>
                or click to browse files (Up to 50MB)
              </p>
            </>
          )}
        </div>

        <button
          className="btn btn-primary"
          style={{ width: '100%', padding: '12px' }}
          disabled={!file || loading}
          onClick={handleUpload}
        >
          {loading ? (
            <>
              <Loader2 size={18} className="spinner" />
              <span>Uploading & Extracting Metadata...</span>
            </>
          ) : (
            'Add Book to Library'
          )}
        </button>
      </div>
    </div>
  );
};
