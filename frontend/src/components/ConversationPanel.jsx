import { useState, useRef, useEffect } from 'react'
import { Send, MessageSquare } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const SUGGESTIONS = [
  'Investigate the high temperature alarm on AHU-01',
  'What is BACnet?',
  'Show energy usage for Chiller-01',
  'Full diagnostics report for AHU-01',
]

export default function ConversationPanel({ messages, onSend, isProcessing, executionPlan }) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || isProcessing) return
    onSend(trimmed)
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Auto-submit suggestion (no manual Enter needed)
  const handleSuggestion = (suggestion) => {
    if (isProcessing) return
    onSend(suggestion)
  }

  return (
    <div className="panel panel-conversation">
      <div className="panel-header">
        <MessageSquare size={16} className="panel-header-icon" />
        <h2>Conversation</h2>
      </div>

      <div className="panel-content">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="graph-empty-icon">
                <MessageSquare size={28} color="var(--accent-cyan)" />
              </div>
              <p className="empty-state-text">
                Ask me about building operations —<br />
                alarms, assets, energy, or documentation.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
                {SUGGESTIONS.map((suggestion, i) => (
                  <button
                    key={i}
                    id={`suggestion-${i}`}
                    onClick={() => handleSuggestion(suggestion)}
                    disabled={isProcessing}
                    style={{
                      padding: '10px 14px',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--text-secondary)',
                      cursor: isProcessing ? 'not-allowed' : 'pointer',
                      fontSize: '12px',
                      textAlign: 'left',
                      fontFamily: 'var(--font-primary)',
                      transition: 'all 0.15s ease',
                      opacity: isProcessing ? 0.5 : 1,
                    }}
                    onMouseEnter={(e) => {
                      if (!isProcessing) {
                        e.currentTarget.style.borderColor = 'var(--accent-cyan)'
                        e.currentTarget.style.color = 'var(--text-primary)'
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--glass-border)'
                      e.currentTarget.style.color = 'var(--text-secondary)'
                    }}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role}`}>
              <span className="chat-message-label">
                {msg.role === 'user' ? 'You' : 'AgenticOS'}
              </span>
              {msg.role === 'user' ? (
                <div className="chat-bubble user">{msg.content}</div>
              ) : (
                /* react-markdown: safe rendering, no dangerouslySetInnerHTML */
                <div className="chat-bubble assistant markdown-body">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              )}
            </div>
          ))}

          {isProcessing && (
            <div className="chat-message assistant">
              <span className="chat-message-label">AgenticOS</span>
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            id="chat-input"
            className="chat-input"
            placeholder="Ask about building operations..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isProcessing}
            rows={1}
          />
          <button
            id="send-btn"
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}
