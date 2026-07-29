import React, { useState } from 'react';
import type { BookRecommendation } from '../types';
import { useBookStore } from '../store/bookStore';
import { api } from '../utils/api';
import { Sparkles, Download, BookOpen, Loader2 } from 'lucide-react';

export const RecommendationPanel: React.FC = () => {
  const { books } = useBookStore();
  const [recommendations, setRecommendations] = useState<BookRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);

  const fetchRecommendations = async () => {
    if (books.length === 0) return;
    setLoading(true);
    try {
      const res = await api.get('/recommend/');
      setRecommendations(res.data.recommendations || []);
      setHasFetched(true);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ margin: '32px 0' }}>
      <div className="flex items-center justify-between" style={{ marginBottom: '20px' }}>
        <div>
          <div className="section-label">AI Analysis</div>
          <h2 className="serif" style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            Smart Recommendations
          </h2>
        </div>

        <button
          className="btn btn-primary"
          onClick={fetchRecommendations}
          disabled={loading || books.length === 0}
          style={{ opacity: books.length === 0 ? 0.6 : 1 }}
        >
          {loading ? (
            <>
              <Loader2 size={16} className="spinner" />
              <span>Analyzing Library...</span>
            </>
          ) : (
            <>
              <Sparkles size={16} />
              <span>{hasFetched ? 'Refresh Recommendations' : 'Analyze & Recommend'}</span>
            </>
          )}
        </button>
      </div>

      {books.length === 0 && (
        <div
          className="glass"
          style={{
            padding: '24px',
            textAlign: 'center',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--color-text-muted)',
            fontSize: '0.9rem',
          }}
        >
          Upload books to your shelf first to get AI-analyzed recommendations based on your favorite genres and authors.
        </div>
      )}

      {/* Grid of Recommended Books */}
      {recommendations.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))',
            gap: '20px',
          }}
        >
          {recommendations.map((rec: BookRecommendation, index: number) => (
            <div
              key={index}
              className="glass"
              style={{
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                transition: 'transform var(--transition-base)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-4px)')}
              onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
            >
              {/* Cover */}
              <div style={{ height: '220px', position: 'relative', overflow: 'hidden', background: 'var(--color-surface-2)' }}>
                {rec.cover_url ? (
                  <img
                    src={rec.cover_url}
                    alt={rec.title}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <div
                    style={{
                      width: '100%',
                      height: '100%',
                      padding: '16px',
                      background: 'linear-gradient(135deg, #1e293b, #0f172a)',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center',
                      textAlign: 'center',
                    }}
                  >
                    <BookOpen size={24} style={{ margin: '0 auto 8px', color: 'var(--color-primary)' }} />
                    <h4 style={{ fontSize: '0.85rem', fontWeight: 600 }}>{rec.title}</h4>
                  </div>
                )}

                {/* Source Badge */}
                <div
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    padding: '2px 6px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(0,0,0,0.7)',
                    backdropFilter: 'blur(4px)',
                    fontSize: '0.65rem',
                    color: rec.source === 'gutenberg' ? '#22c55e' : '#3b82f6',
                    fontWeight: 600,
                  }}
                >
                  {rec.source === 'gutenberg' ? 'Free Public Domain' : 'Open Library'}
                </div>
              </div>

              {/* Book Info & Action */}
              <div style={{ padding: '12px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <h4
                    style={{
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      lineHeight: '1.3',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={rec.title}
                  >
                    {rec.title}
                  </h4>
                  <p
                    className="text-muted"
                    style={{
                      fontSize: '0.75rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      marginBottom: '10px',
                    }}
                  >
                    {rec.author || 'Unknown Author'}
                  </p>
                </div>

                {/* Download / View Button */}
                {rec.download_url ? (
                  <a
                    href={rec.download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary"
                    style={{ width: '100%', padding: '6px 10px', fontSize: '0.75rem' }}
                  >
                    <Download size={14} />
                    <span>Download PDF</span>
                  </a>
                ) : (
                  <div
                    className="text-faint flex items-center justify-center gap-1"
                    style={{ fontSize: '0.72rem', padding: '6px 0' }}
                  >
                    <span>Cover only (No PDF)</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
