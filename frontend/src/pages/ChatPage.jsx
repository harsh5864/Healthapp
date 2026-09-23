import { useEffect, useState, useRef } from 'react';
import { chatApi } from '../services/appServices';

export default function ChatPage() {
  const [conversations, setConversations] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    chatApi.conversations()
      .then((r) => {
        setConversations(r.data);
        if (r.data && r.data[0]) {
          open(r.data[0]);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const open = (c) => {
    setActive(c);
    setError('');
    chatApi.messages(c.id)
      .then((r) => setMessages(r.data))
      .catch(() => {
        setError('Could not load messages for this conversation.');
      });
  };

  const newChat = async () => {
    try {
      setError('');
      const c = (await chatApi.create('New Health Chat')).data;
      setConversations((prev) => [c, ...prev]);
      setActive(c);
      setMessages([]);
    } catch (err) {
      setError('Could not create a new conversation. Please try again.');
    }
  };

  const deleteChat = async (id, e) => {
    e.stopPropagation();
    try {
      setError('');
      await chatApi.remove(id);
      const updated = conversations.filter((c) => c.id !== id);
      setConversations(updated);
      if (active?.id === id) {
        if (updated.length > 0) {
          open(updated[0]);
        } else {
          setActive(null);
          setMessages([]);
        }
      }
    } catch (err) {
      setError('Could not delete the conversation. Please try again.');
    }
  };

  const send = async (e) => {
    e.preventDefault();
    const userText = text.trim();
    if (!userText || !active || loading) return;

    // Optimistic UI update: display user message immediately
    const tempUserMsg = {
      id: 'temp-' + Date.now(),
      sender: 'USER',
      message: userText,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setText('');
    setLoading(true);
    setError('');

    try {
      const response = await chatApi.send(active.id, userText);
      setMessages(response.data);

      // Refresh conversations list in background to reflect updated title & timestamps
      chatApi.conversations()
        .then((r) => {
          setConversations(r.data);
          const current = r.data.find((item) => item.id === active.id);
          if (current) setActive(current);
        })
        .catch(() => {});
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Sorry, I could not process that message right now. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page-content chat-page">
      <div className="page-heading compact">
        <div>
          <p className="eyebrow">💬 Smart health chat</p>
          <h1>A thoughtful place to ask.</h1>
        </div>
        <button className="button button--secondary" onClick={newChat}>
          + New conversation
        </button>
      </div>

      <div className="chat-layout">
        <aside className="conversation-list">
          <h3>Conversations</h3>
          {conversations.map((c) => (
            <div
              className={`conversation-item ${active?.id === c.id ? 'selected' : ''}`}
              key={c.id}
            >
              <button
                className="conversation-title-btn"
                title={c.title}
                onClick={() => open(c)}
              >
                {c.title}
              </button>
              <button
                className="conversation-delete-btn"
                title="Delete conversation"
                aria-label={`Delete ${c.title}`}
                onClick={(e) => deleteChat(c.id, e)}
              >
                &times;
              </button>
            </div>
          ))}
          {!conversations.length && <small>No conversations yet.</small>}
        </aside>

        <div className="chat-window">
          <div className="chat-messages">
            {!active ? (
              <div className="chat-empty">
                <span>✦</span>
                <h2>Start a conversation</h2>
                <p>
                  Ask about symptoms, healthy habits, or what to discuss with a clinician.
                </p>
                <button className="button button--primary" onClick={newChat}>
                  Start chat
                </button>
              </div>
            ) : (
              messages.map((m) => (
                <div
                  className={`message message--${(m.sender || 'user').toLowerCase()}`}
                  key={m.id}
                >
                  <span>{m.sender === 'AI' ? '✦' : 'You'}</span>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{m.message}</p>
                </div>
              ))
            )}
            {loading && (
              <div className="message message--ai">
                <span>✦</span>
                <p className="typing">Thinking…</p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {active && (
            <form className="chat-input" onSubmit={send}>
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Ask a general health question…"
                disabled={loading}
              />
              <button
                className="button button--primary"
                disabled={loading || !text.trim()}
              >
                Send
              </button>
            </form>
          )}

          <p className="chat-disclaimer">
            Medical disclaimer: This AI provides general educational health information and
            is not a substitute for professional medical advice, diagnosis, or treatment. Seek
            immediate emergency care for severe or life-threatening symptoms.
          </p>
          {error && <div className="form-error">{error}</div>}
        </div>
      </div>
    </section>
  );
}
