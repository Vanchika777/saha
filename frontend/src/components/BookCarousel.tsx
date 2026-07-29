import React, { useRef } from 'react';
import { useBookStore } from '../store/bookStore';
import { BookCard } from './BookCard';
import { Plus, ChevronLeft, ChevronRight, BookOpen } from 'lucide-react';
import { api } from '../utils/api';

export const BookCarousel: React.FC = () => {
  const { books, selectedBookIds, toggleBookSelection, removeBook, openUploadModal } = useBookStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const scrollAmount = direction === 'left' ? -300 : 300;
      scrollRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  const handleDelete = async (bookId: string) => {
    if (!confirm('Are you sure you want to delete this book?')) return;
    try {
      await api.delete(`/books/${bookId}`);
      removeBook(bookId);
    } catch (err) {
      alert('Failed to delete book');
    }
  };

  return (
    <div style={{ position: 'relative', margin: '24px 0' }}>
      <div className="flex items-center justify-between" style={{ marginBottom: '16px' }}>
        <div>
          <div className="section-label">Your Shelf</div>
          <h2 className="serif" style={{ fontSize: '1.5rem' }}>
            Book Library ({books.length})
          </h2>
        </div>

        {/* Carousel Navigation Buttons */}
        {books.length > 0 && (
          <div className="flex items-center gap-2">
            <button
              className="btn btn-ghost btn-icon"
              onClick={() => scroll('left')}
              title="Scroll left"
            >
              <ChevronLeft size={18} />
            </button>
            <button
              className="btn btn-ghost btn-icon"
              onClick={() => scroll('right')}
              title="Scroll right"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        )}
      </div>

      {/* Horizontal Carousel Track */}
      <div
        ref={scrollRef}
        style={{
          display: 'flex',
          gap: '20px',
          overflowX: 'auto',
          paddingBottom: '16px',
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
        }}
      >
        {/* Upload Card */}
        <div
          onClick={openUploadModal}
          style={{
            width: '180px',
            height: '260px',
            flexShrink: 0,
            borderRadius: 'var(--radius-lg)',
            border: '2px dashed var(--color-border)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            cursor: 'pointer',
            background: 'rgba(255, 255, 255, 0.02)',
            transition: 'all var(--transition-base)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-primary)')}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '50%',
              background: 'var(--color-surface-2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-primary)',
            }}
          >
            <Plus size={22} />
          </div>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
            Upload PDF
          </span>
        </div>

        {/* Uploaded Books List */}
        {books.map((book) => (
          <BookCard
            key={book.id}
            book={book}
            isSelected={selectedBookIds.includes(book.id)}
            onSelect={() => toggleBookSelection(book.id)}
            onDelete={() => handleDelete(book.id)}
          />
        ))}

        {books.length === 0 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              padding: '24px 32px',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border)',
              minWidth: '350px',
            }}
          >
            <BookOpen size={32} color="var(--color-primary)" />
            <div>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Your shelf is empty</h4>
              <p className="text-muted" style={{ fontSize: '0.8rem' }}>
                Upload a book PDF to enable RAG chat & personalized recommendations.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
