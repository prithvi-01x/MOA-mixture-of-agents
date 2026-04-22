import { useEffect, useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, Wrench, Plus, Menu, X } from 'lucide-react';
import { useStore } from '../store/app';
import { api } from '../lib/api';

const NAV = [
  { to: '/setup', label: 'WORKBENCH', icon: Wrench },
  { to: '/chat', label: 'AGENTS', icon: MessageSquare },
];

export default function AppLayout() {
  const {
    conversations, health, activeConversationId,
    setHealth, setConversations, setGroqModels, setOpenRouterModels,
    setActiveConversationId, newChat,
    theme, toggleTheme,
  } = useStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    api.groqModels().then((r) => setGroqModels(r.models)).catch(() => {});
    api.openrouterModels().then((r) => setOpenRouterModels(r.models)).catch(() => {});
    api.conversations().then(setConversations).catch(() => {});
  }, [setHealth, setGroqModels, setOpenRouterModels, setConversations]);

  const onSetup = location.pathname === '/setup' || location.pathname === '/';

  const handleConversationClick = (id: string) => {
    setActiveConversationId(id);
    navigate('/chat');
    setSidebarOpen(false);
  };

  const handleNewChat = () => {
    newChat();
    navigate('/setup');
    setSidebarOpen(false);
  };

  const sidebar = (
    <aside
      id="main-sidebar"
      style={{
        width: 208,
        background: 'var(--bg-panel)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        height: '100%',
      }}
    >
      {/* Brand */}
      <div style={{ padding: '20px 16px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontFamily: 'var(--font-headline)', fontWeight: 700, fontSize: 24, color: 'var(--accent)', letterSpacing: '-0.02em' }}>
          MOA
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-dim)', marginTop: 2, letterSpacing: '0.08em' }}>
          mixture of agents
        </div>
      </div>

      {/* New Chat */}
      <div style={{ padding: '12px 16px' }}>
        <button
          onClick={handleNewChat}
          id="new-chat-btn"
          style={{
            width: '100%',
            padding: '8px 12px',
            background: 'transparent',
            border: '1px solid var(--border-mid)',
            color: 'var(--accent)',
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '0.08em',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <Plus size={12} />
          NEW CHAT
        </button>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '4px 0', overflowY: 'auto' }}>
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setSidebarOpen(false)}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 16px',
              textDecoration: 'none',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 500,
              letterSpacing: '0.08em',
              color: isActive ? 'var(--accent)' : 'var(--text-dim)',
              borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
              background: isActive ? 'var(--accent-dim)' : 'transparent',
            })}
          >
            <Icon size={13} />
            {label}
          </NavLink>
        ))}

        {/* Recent Conversations */}
        <div style={{
          padding: '16px 16px 8px',
          fontFamily: 'var(--font-mono)',
          fontSize: 9,
          color: 'var(--text-dim)',
          letterSpacing: '0.1em',
        }}>
          RECENT CHATS
        </div>

        {conversations.length === 0 && (
          <div style={{
            padding: '4px 16px',
            fontFamily: 'var(--font-mono)',
            fontSize: 9,
            color: 'var(--text-dim)',
            opacity: 0.5,
          }}>
            No conversations yet
          </div>
        )}

        {conversations.slice(0, 12).map((c) => {
          const isActive = c.id === activeConversationId;
          return (
            <div
              key={c.id}
              onClick={() => handleConversationClick(c.id)}
              title={c.title}
              style={{
                padding: '7px 16px',
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: isActive ? 'var(--accent)' : 'var(--text-dim)',
                background: isActive ? 'var(--accent-dim)' : 'transparent',
                borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                cursor: 'pointer',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                transition: 'background 0.1s, color 0.1s',
              }}
              onMouseEnter={(e) => {
                if (!isActive) (e.currentTarget as HTMLDivElement).style.color = 'var(--text)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) (e.currentTarget as HTMLDivElement).style.color = 'var(--text-dim)';
              }}
            >
              {c.title}
            </div>
          );
        })}
      </nav>

      {/* Health + Footer */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          {(['groq', 'openrouter'] as const).map((p) => (
            <div key={p} style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
              <div style={{
                width: 5, height: 5,
                background: health[p] ? 'var(--accent)' : '#444',
                borderRadius: '50% !important' as unknown as string,
              }} className={health[p] ? 'pulse' : ''} />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                {p.slice(0, 3)}
              </span>
            </div>
          ))}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)', letterSpacing: '0.05em' }}>
          V1.1.0_STABLE
        </div>
      </div>
    </aside>
  );

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)' }}>
      {/* Desktop sidebar — always visible ≥768px */}
      <div className="desktop-sidebar">
        {sidebar}
      </div>

      {/* Mobile overlay sidebar */}
      {sidebarOpen && (
        <>
          {/* Backdrop */}
          <div
            onClick={() => setSidebarOpen(false)}
            style={{
              position: 'fixed', inset: 0, zIndex: 40,
              background: 'rgba(0,0,0,0.6)',
            }}
          />
          {/* Drawer */}
          <div style={{
            position: 'fixed', top: 0, left: 0, bottom: 0,
            width: 208, zIndex: 50,
          }}>
            {sidebar}
          </div>
        </>
      )}

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        {/* Top bar */}
        <header style={{
          height: 48,
          background: 'var(--bg-panel)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          flexShrink: 0,
          gap: 12,
        }}>
          {/* Hamburger — only visible on mobile */}
          <button
            id="hamburger-btn"
            onClick={() => setSidebarOpen(v => !v)}
            className="mobile-only"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-dim)',
              cursor: 'pointer',
              padding: 4,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>

          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, color: 'var(--text)', letterSpacing: '0.06em' }}>
            MOA_WORKBENCH
          </span>

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Theme toggle */}
            <button
              id="theme-toggle-btn"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              style={{
                background: 'transparent',
                border: '1px solid var(--border-mid)',
                color: 'var(--text-dim)',
                fontFamily: 'var(--font-mono)',
                fontSize: 14,
                cursor: 'pointer',
                padding: '3px 8px',
                lineHeight: 1,
              }}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </header>

        {/* Page content */}
        <div style={{ flex: 1, overflow: onSetup ? 'auto' : 'hidden' }}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
