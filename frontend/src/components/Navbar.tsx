import React from 'react';
import { useAuthStore } from '../store/authStore';
import { BookOpen, LogIn, LogOut, User as UserIcon } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, openAuthModal, logout } = useAuthStore();

  // Safely extract display name without triggering TypeScript errors on missing properties
  const rawUser = user as Record<string, any> | null;
  const displayName = 
    rawUser?.display_name || 
    rawUser?.name || 
    (user?.email ? user.email.split('@')[0] : 'User');

  return (
    <header style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      height: '72px',
      background: 'rgba(252, 245, 238, 0.85)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--color-border)',
      zIndex: 100,
      display: 'flex',
      alignItems: 'center'
    }}>
      <div className="container flex items-center justify-between" style={{ width: '100%', maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, var(--color-dark), var(--color-primary))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px rgba(133, 14, 53, 0.25)'
          }}>
            <BookOpen size={20} color="#FCF5EE" />
          </div>
          <div>
            <span className="serif text-dark" style={{ fontSize: '1.4rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
              saha
            </span>
            <span className="badge badge-processing" style={{ marginLeft: '8px', fontSize: '0.65rem' }}>
              AI Book Companion
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3" style={{ background: 'var(--color-surface-2)', padding: '6px 14px', borderRadius: 'var(--radius-full)', border: '1px solid var(--color-border)' }}>
              {rawUser?.avatar_url ? (
                <img src={rawUser.avatar_url} alt={displayName} style={{ width: '28px', height: '28px', borderRadius: '50%' }} />
              ) : (
                <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UserIcon size={14} color="#ffffff" />
                </div>
              )}
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{displayName}</span>
              <button
                onClick={logout}
                title="Logout"
                style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center' }}
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <button
              className="btn btn-primary flex items-center gap-2"
              onClick={() => openAuthModal('login')}
            >
              <LogIn size={16} />
              <span>Sign In / Sign Up</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};