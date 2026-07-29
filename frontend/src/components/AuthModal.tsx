import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '../store/authStore';
import { api } from '../utils/api';
import { X, Mail, Lock, User as UserIcon } from 'lucide-react';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, authModalMode, closeAuthModal, openAuthModal, setUser } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = authModalMode === 'login' ? '/auth/login' : '/auth/register';
      const payload = authModalMode === 'login'
        ? { email, password }
        : { email, password, display_name: displayName };

      const res = await api.post(endpoint, payload);
      const { user, token } = res.data;

      setUser(user, token);
      closeAuthModal();
      setEmail('');
      setPassword('');
      setDisplayName('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = () => {
    const width = 500;
    const height = 600;
    const left = window.screen.width / 2 - width / 2;
    const top = window.screen.height / 2 - height / 2;

    window.open(
      'http://localhost:5000/api/auth/google',
      'Google Login',
      `width=${width},height=${height},top=${top},left=${left}`
    );

    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'GOOGLE_AUTH_SUCCESS' && event.data?.token) {
        localStorage.setItem('saha_token', event.data.token);
        api.get('/auth/me').then((res) => {
          setUser(res.data.user, event.data.token);
          closeAuthModal();
        });
        window.removeEventListener('message', handleMessage);
      }
    };

    window.addEventListener('message', handleMessage);
  };

  return (
    <AnimatePresence>
      <div className="backdrop" onClick={closeAuthModal}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.2 }}
          className="glass"
          style={{
            width: '100%',
            maxWidth: '420px',
            padding: '32px',
            position: 'relative',
            borderRadius: 'var(--radius-xl)',
            background: 'var(--color-surface)',
            boxShadow: 'var(--shadow-lg)'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close button */}
          <button
            onClick={closeAuthModal}
            style={{
              position: 'absolute',
              top: '20px',
              right: '20px',
              color: 'var(--color-text-muted)',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>

          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <h2 className="serif" style={{ fontSize: '1.75rem', marginBottom: '6px' }}>
              {authModalMode === 'login' ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>
              {authModalMode === 'login'
                ? 'Sign in to sync your library and chat history'
                : 'Save your books and recommendations permanently'}
            </p>
          </div>

          {error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#ef4444',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
              marginBottom: '16px'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {authModalMode === 'register' && (
              <div>
                <label className="text-muted" style={{ fontSize: '0.8rem', display: 'block', marginBottom: '6px' }}>
                  Display Name
                </label>
                <div style={{ position: 'relative' }}>
                  <UserIcon size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--color-text-muted)' }} />
                  <input
                    className="input"
                    type="text"
                    placeholder="e.g. Jane Austen"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    style={{ paddingLeft: '40px' }}
                    required
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-muted" style={{ fontSize: '0.8rem', display: 'block', marginBottom: '6px' }}>
                Email Address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--color-text-muted)' }} />
                <input
                  className="input"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{ paddingLeft: '40px' }}
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-muted" style={{ fontSize: '0.8rem', display: 'block', marginBottom: '6px' }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--color-text-muted)' }} />
                <input
                  className="input"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ paddingLeft: '40px' }}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ marginTop: '8px', padding: '12px' }}
            >
              {loading ? <div className="spinner" /> : (authModalMode === 'login' ? 'Sign In' : 'Create Account')}
            </button>
          </form>

          <div style={{ display: 'flex', alignItems: 'center', margin: '20px 0' }}>
            <div className="divider" style={{ flex: 1 }} />
            <span className="text-faint" style={{ fontSize: '0.75rem', padding: '0 12px' }}>OR</span>
            <div className="divider" style={{ flex: 1 }} />
          </div>

          <button
            type="button"
            className="btn btn-ghost"
            style={{ width: '100%', padding: '10px' }}
            onClick={handleGoogleAuth}
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z" />
              <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z" />
              <path fill="#FBBC05" d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 10.8 0 12.5s.7 2.8 1.9 5.2l3.7-2.9z" />
              <path fill="#34A853" d="M12 24c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 17C3.7 20.7 7.5 24 12 24z" />
            </svg>
            <span>Continue with Google</span>
          </button>

          <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '0.85rem' }} className="text-muted">
            {authModalMode === 'login' ? (
              <>
                Don't have an account?{' '}
                <button
                  onClick={() => openAuthModal('register')}
                  style={{ color: 'var(--color-primary)', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  Sign Up
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button
                  onClick={() => openAuthModal('login')}
                  style={{ color: 'var(--color-primary)', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  Sign In
                </button>
              </>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
