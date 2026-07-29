import React, { useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { BookCarousel } from '../components/BookCarousel';
import { RecommendationPanel } from '../components/RecommendationPanel';
import { ChatWindow } from '../components/ChatWindow';
import { AuthModal } from '../components/AuthModal';
import { UploadModal } from '../components/UploadModal';
import { useAuthStore } from '../store/authStore';
import { useBookStore } from '../store/bookStore';
import { api } from '../utils/api';
import { Sparkles } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { token, setUser } = useAuthStore();
  const { setBooks } = useBookStore();

  useEffect(() => {
    // 1. Fetch user info if token exists
    if (token) {
      api
        .get('/auth/me')
        .then((res) => setUser(res.data.user))
        .catch(() => setUser(null, null));
    }

    // 2. Load books
    api
      .get('/books/')
      .then((res) => setBooks(res.data.books || []))
      .catch(() => setBooks([]));
  }, [token]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <main className="container page-content" style={{ flex: 1 }}>
        {/* Hero Welcome Banner */}
        <section style={{ margin: '32px 0 24px 0', textAlign: 'center' }}>
          <div
            className="badge badge-processing"
            style={{ marginBottom: '12px', padding: '6px 14px', fontSize: '0.75rem' }}
          >
            <Sparkles size={14} style={{ marginRight: '6px' }} />
            <span>Next-Gen Enterprise Book Companion</span>
          </div>
          <h1 className="serif" style={{ marginBottom: '12px' }}>
            Talk to your <span className="text-gradient">Book Library</span>
          </h1>
          <p
            className="text-muted"
            style={{ maxWidth: '640px', margin: '0 auto', fontSize: '1.05rem', lineHeight: '1.6' }}
          >
            Upload your PDFs, store your entire library, get smart genre & author recommendations, and have deep AI-powered conversations with your books.
          </p>
        </section>

        {/* 1. Book Shelf / Carousel */}
        <BookCarousel />

        {/* 2. Recommendation Engine Panel */}
        <RecommendationPanel />

        {/* 3. Highlight AI RAG Chat Window */}
        <ChatWindow />
      </main>

      {/* Modals */}
      <AuthModal />
      <UploadModal />

      {/* Ambient background glow */}
      <div className="ambient-glow" />
    </div>
  );
};
