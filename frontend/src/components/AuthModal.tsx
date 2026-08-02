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
        : { email, password, display_name: displayName, name: displayName };

      const res = await api.post(endpoint, payload);
      const { user, token } = res.data;

      setUser(user, token);
      closeAuthModal();
      setEmail('');
      setPassword('');
      setDisplayName('');
    } catch (err: any) {
      setError(
        err.response?.data?.error || 
        err.response?.data?.detail || 
        'Authentication failed. Please check your credentials.'
      );
    } finally {
      setLoading(false);
    }
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
            type="button"
            style={{
              position: 'absolute',
              top: '20px',
              right: '20px',
              color: 'var(--color-text-muted)',
              padding: '4px',
              background: 'none',
              border: 'none',
              cursor: 'pointer'
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
                    placeholder="e.g. Vanchika Raghav"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    style={{ paddingLeft: '40px', width: '100%' }}
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
                  style={{ paddingLeft: '40px', width: '100%' }}
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
                  style={{ paddingLeft: '40px', width: '100%' }}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ marginTop: '8px', padding: '12px', width: '100%' }}
            >
              {loading ? <div className="spinner" /> : (authModalMode === 'login' ? 'Sign In' : 'Create Account')}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '0.85rem' }} className="text-muted">
            {authModalMode === 'login' ? (
              <>
                Don't have an account?{' '}
                <button
                  type="button"
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
                  type="button"
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