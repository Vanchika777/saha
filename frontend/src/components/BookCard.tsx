import React from 'react';
import type { Book } from '../types';
import { Book as BookIcon, Check, Trash2, Loader2 } from 'lucide-react';

interface BookCardProps {
  book: Book;
  isSelected: boolean;
  onSelect: () => void;
  onDelete?: () => void;
}

export const BookCard: React.FC<BookCardProps> = ({ book, isSelected, onSelect, onDelete }) => {
  return (
    <div
      onClick={onSelect}
      style={{
        width: '180px',
        flexShrink: 0,
        cursor: 'pointer',
        position: 'relative',
        userSelect: 'none',
      }}
    >
      {/* Book Cover Container */}
      <div
        style={{
          width: '180px',
          height: '260px',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          position: 'relative',
          background: 'linear-gradient(135deg, var(--color-surface-2), var(--color-surface-3))',
          border: isSelected ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
          boxShadow: isSelected ? '0 0 25px var(--color-primary-glow)' : 'var(--shadow-md)',
          transition: 'all var(--transition-base)',
        }}
      >
        {book.cover_url ? (
          <img
            src={book.cover_url}
            alt={book.title}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          /* Placeholder Cover with Title & Gradient */
          <div
            style={{
              width: '100%',
              height: '100%',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'linear-gradient(145deg, var(--color-dark), var(--color-primary))',
              color: '#FCF5EE',
            }}
          >
            <div>
              <BookIcon size={24} style={{ opacity: 0.8, marginBottom: '12px' }} />
              <h4 className="serif" style={{ fontSize: '1rem', lineHeight: '1.3', fontWeight: 600 }}>
                {book.title}
              </h4>
            </div>
            <p style={{ fontSize: '0.75rem', opacity: 0.7 }}>{book.author || 'Unknown Author'}</p>
          </div>
        )}

        {/* Selected Checkmark Overlay */}
        {isSelected && (
          <div
            style={{
              position: 'absolute',
              top: '10px',
              right: '10px',
              width: '26px',
              height: '26px',
              borderRadius: '50%',
              background: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 10px rgba(0,0,0,0.5)',
            }}
          >
            <Check size={16} color="#ffffff" />
          </div>
        )}

        {/* Status Badge Overlay */}
        {book.embedding_status !== 'done' && (
          <div
            style={{
              position: 'absolute',
              bottom: '10px',
              left: '10px',
              right: '10px',
              padding: '4px 8px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(0,0,0,0.75)',
              backdropFilter: 'blur(4px)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.7rem',
            }}
          >
            {book.embedding_status === 'processing' && (
              <>
                <Loader2 size={12} className="spinner" style={{ borderTopColor: 'var(--color-info)' }} />
                <span style={{ color: 'var(--color-info)' }}>Indexing...</span>
              </>
            )}
            {book.embedding_status === 'pending' && (
              <span className="text-muted">Queued...</span>
            )}
            {book.embedding_status === 'failed' && (
              <span style={{ color: 'var(--color-error)' }}>Processing Failed</span>
            )}
          </div>
        )}

        {/* Hover Delete Action */}
        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            title="Delete book"
            style={{
              position: 'absolute',
              top: '10px',
              left: '10px',
              width: '28px',
              height: '28px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(0,0,0,0.6)',
              color: '#ef4444',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>

      {/* Book Meta Info below card */}
      <div style={{ marginTop: '10px' }}>
        <h4
          style={{
            fontSize: '0.88rem',
            fontWeight: 600,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={book.title}
        >
          {book.title}
        </h4>
        <p
          className="text-muted"
          style={{
            fontSize: '0.78rem',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {book.author || 'Unknown Author'}
        </p>
      </div>
    </div>
  );
};
