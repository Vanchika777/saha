import React from 'react';
import type { ChatMessage as ChatMessageType } from '../types';
import { Bot, User, BookOpen } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        margin: '16px 0',
        alignItems: 'flex-start',
        flexDirection: isUser ? 'row-reverse' : 'row',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          background: isUser
            ? 'var(--color-primary)'
            : 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: isUser ? 'none' : '0 2px 10px var(--color-primary-glow)',
        }}
      >
        {isUser ? <User size={16} color="#ffffff" /> : <Bot size={16} color="#ffffff" />}
      </div>

      {/* Message Bubble */}
      <div
        style={{
          maxWidth: '75%',
          padding: '12px 16px',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          background: isUser ? 'var(--color-primary)' : 'var(--color-surface-2)',
          color: isUser ? '#ffffff' : 'var(--color-text)',
          border: isUser ? 'none' : '1px solid var(--color-border)',
          fontSize: '0.92rem',
          lineHeight: '1.5',
          whiteSpace: 'pre-wrap',
        }}
      >
        {message.content}

        {/* Source Citations */}
        {message.sources && message.sources.length > 0 && (
          <div
            style={{
              marginTop: '10px',
              paddingTop: '8px',
              borderTop: '1px solid rgba(255,255,255,0.1)',
              fontSize: '0.75rem',
            }}
          >
            <div className="flex items-center gap-1 text-faint" style={{ marginBottom: '4px' }}>
              <BookOpen size={12} />
              <span>Referenced Sources:</span>
            </div>
            {message.sources.map((src, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  marginTop: '4px',
                }}
              >
                <span style={{ fontWeight: 600, color: 'var(--color-accent)' }}>
                  '{src.book_title}'
                </span>
                {src.text_snippet && (
                  <p className="text-muted" style={{ fontStyle: 'italic', marginTop: '2px' }}>
                    "{src.text_snippet}..."
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
