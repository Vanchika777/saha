import React, { useState, useEffect, useRef } from 'react';
import { useChatStore } from '../store/chatStore';
import { useBookStore } from '../store/bookStore';
import { ChatMessage } from './ChatMessage';
import { api, API_BASE_URL } from '../utils/api';
import { Send, Bot, RefreshCw } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../types';

export const ChatWindow: React.FC = () => {
  const { currentSession, messages, isStreaming, activeStreamToken, setCurrentSession, addMessage, setIsStreaming, appendStreamToken, clearStreamToken } = useChatStore();
  const { books, selectedBookIds } = useBookStore();
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeStreamToken]);

  useEffect(() => {
    if (!currentSession) {
      initSession();
    }
  }, []);

  const initSession = async () => {
    try {
      const res = await api.post('/chat/sessions', {
        book_ids: selectedBookIds.length > 0 ? selectedBookIds : books.map((b) => b.id),
      });
      setCurrentSession(res.data.session);
    } catch (err) {
      console.error('Failed to create chat session', err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isStreaming) return;

    const userText = inputMessage.trim();
    setInputMessage('');

    const targetBookIds = selectedBookIds.length > 0 ? selectedBookIds : books.map((b) => b.id);

    const userMsg: ChatMessageType = {
      id: Date.now().toString(),
      role: 'user',
      content: userText,
      timestamp: new Date().toISOString(),
    };
    addMessage(userMsg);

    let sessionId = currentSession?.session_id;
    if (!sessionId) {
      try {
        const res = await api.post('/chat/sessions', { book_ids: targetBookIds });
        setCurrentSession(res.data.session);
        sessionId = res.data.session.session_id;
      } catch (err) {
        alert('Could not start chat session');
        return;
      }
    }

    setIsStreaming(true);
    clearStreamToken();

    try {
      const token = localStorage.getItem('saha_token');
      const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: userText,
          book_ids: targetBookIds,
          stream: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Streaming failed');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulated = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.replace('data: ', ''));
                if (data.type === 'token') {
                  accumulated += data.content;
                  appendStreamToken(data.content);
                } else if (data.type === 'done') {
                  const botMsg: ChatMessageType = {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: accumulated || data.full_response,
                    timestamp: new Date().toISOString(),
                  };
                  addMessage(botMsg);
                  clearStreamToken();
                  setIsStreaming(false);
                }
              } catch (e) {
                // ignore partial frames
              }
            }
          }
        }
      }
    } catch (err) {
      console.error('Streaming error:', err);
      setIsStreaming(false);
      clearStreamToken();
    }
  };

  return (
    <div style={{ margin: '24px 0 48px 0' }}>
      <div className="flex items-center justify-between" style={{ marginBottom: '16px' }}>
        <div>
          <div className="section-label">AI Chat</div>
          <h2 className="serif text-dark" style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            Book Conversation
          </h2>
        </div>

        <button
          className="btn btn-ghost btn-icon"
          onClick={initSession}
          title="New Conversation"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      {/* Compact Chat Block */}
      <div
        className="glass"
        style={{
          borderRadius: 'var(--radius-xl)',
          display: 'flex',
          flexDirection: 'column',
          height: '360px',
          overflow: 'hidden',
          border: '1px solid var(--color-border)',
          background: 'var(--color-surface)',
        }}
      >
        {/* Messages Stream Area */}
        <div
          style={{
            flex: 1,
            padding: '16px 20px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            background: 'var(--color-surface-2)',
          }}
        >
          {messages.length === 0 && !isStreaming && (
            <div
              style={{
                margin: 'auto',
                textAlign: 'center',
                maxWidth: '420px',
                color: 'var(--color-text-muted)',
              }}
            >
              <Bot size={28} color="var(--color-primary)" style={{ margin: '0 auto 8px' }} />
              <h4 className="serif text-dark" style={{ fontSize: '1.1rem', marginBottom: '6px' }}>
                Ask Saha about any book
              </h4>
              <p style={{ fontSize: '0.82rem', lineHeight: '1.4' }}>
                Saha seamlessly accesses your library books, recommended titles, and general literary knowledge.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {isStreaming && activeStreamToken && (
            <ChatMessage
              message={{
                id: 'streaming-msg',
                role: 'assistant',
                content: activeStreamToken,
                timestamp: new Date().toISOString(),
              }}
            />
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form
          onSubmit={handleSendMessage}
          style={{
            padding: '12px 16px',
            borderTop: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            display: 'flex',
            gap: '10px',
            alignItems: 'center',
          }}
        >
          <input
            className="input"
            type="text"
            placeholder="Ask about themes, plot, characters, or any book..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={isStreaming}
            style={{ flex: 1, padding: '10px 14px', fontSize: '0.88rem' }}
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!inputMessage.trim() || isStreaming}
            style={{ padding: '10px 18px', fontSize: '0.85rem' }}
          >
            {isStreaming ? (
              <div className="spinner" style={{ borderTopColor: '#FCF5EE' }} />
            ) : (
              <>
                <Send size={15} />
                <span>Send</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
