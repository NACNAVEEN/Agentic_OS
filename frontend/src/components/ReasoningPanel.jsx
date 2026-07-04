import { useRef, useEffect, useState } from 'react'
import { Brain, Wrench, Activity, ShieldCheck } from 'lucide-react'

/* ── Confidence ring SVG ───────────────────────────────────────────────────── */
function ConfidenceRing({ score }) {
  const pct = Math.round((score || 0) * 100)
  const r = 26
  const circ = 2 * Math.PI * r
  const dash = (pct / 100) * circ
  const color = pct >= 80 ? 'var(--accent-green)' : pct >= 50 ? 'var(--accent-cyan)' : '#ef4444'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={64} height={64} viewBox="0 0 64 64">
        <circle cx={32} cy={32} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={6} />
        <circle
          cx={32} cy={32} r={r} fill="none"
          stroke={color} strokeWidth={6}
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeLinecap="round"
          transform="rotate(-90 32 32)"
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
        <text x={32} y={37} textAnchor="middle" fill={color} fontSize={13} fontWeight={700}
          fontFamily="var(--font-primary)">{pct}%</text>
      </svg>
      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Confidence</span>
    </div>
  )
}

/* ── Gantt timeline ────────────────────────────────────────────────────────── */
function GanttTimeline({ agentStates }) {
  const entries = Object.entries(agentStates).filter(([, s]) => s.executionTime > 0)
  if (entries.length === 0) {
    return (
      <div className="empty-state">
        <Activity size={24} color="var(--text-muted)" />
        <p className="empty-state-text">Agent lifecycle events will<br />appear here in real time.</p>
      </div>
    )
  }
  const maxTime = Math.max(...entries.map(([, s]) => s.executionTime || 1))
  const colors = {
    planner: 'var(--accent-cyan)', asset_agent: '#a78bfa',
    alarm_agent: '#f87171', energy_agent: '#fbbf24',
    documentation_agent: '#34d399', supervisor: '#60a5fa',
    verification: '#f472b6',
  }
  return (
    <div className="gantt-container">
      {entries.map(([name, state]) => {
        const pct = Math.max(4, ((state.executionTime || 1) / maxTime) * 100)
        const color = colors[name] || 'var(--accent-cyan)'
        return (
          <div key={name} className="gantt-row">
            <div className="gantt-label">{state.displayName || name}</div>
            <div className="gantt-track">
              <div
                className="gantt-bar"
                style={{
                  width: `${pct}%`,
                  background: color,
                  opacity: state.status === 'failed' ? 0.4 : 0.85,
                }}
              />
            </div>
            <div className="gantt-time">{state.executionTime?.toFixed(0)}ms</div>
          </div>
        )
      })}
    </div>
  )
}

/* ── Verification tab ──────────────────────────────────────────────────────── */
function VerificationTab({ verificationResult }) {
  if (!verificationResult || !verificationResult.status) {
    return (
      <div className="empty-state">
        <ShieldCheck size={24} color="var(--text-muted)" />
        <p className="empty-state-text">Verification results will appear<br />after the response is generated.</p>
      </div>
    )
  }
  const { status, confidence_score, grounded_claims, ungrounded_claims, claim_coverage } = verificationResult
  const statusColor = status === 'VERIFIED' ? 'var(--accent-green)'
    : status === 'PARTIAL' ? 'var(--accent-cyan)' : '#ef4444'

  return (
    <div className="verification-panel">
      <div className="verification-header">
        <ConfidenceRing score={confidence_score} />
        <div style={{ flex: 1 }}>
          <div className="verification-status" style={{ color: statusColor }}>
            {status === 'VERIFIED' ? '✓ VERIFIED' : status === 'PARTIAL' ? '⚠ PARTIAL' : '✗ UNVERIFIED'}
          </div>
          <div className="verification-meta">{claim_coverage}</div>
          <div className="verification-meta">
            {verificationResult.agents_completed}/{verificationResult.agents_total} agents completed
          </div>
        </div>
      </div>

      {grounded_claims?.length > 0 && (
        <div className="verification-section">
          <div className="verification-section-title" style={{ color: 'var(--accent-green)' }}>
            ✓ Grounded Claims ({grounded_claims.length})
          </div>
          <div className="claim-list">
            {grounded_claims.map((c, i) => (
              <span key={i} className="claim-tag grounded">{c}</span>
            ))}
          </div>
        </div>
      )}

      {ungrounded_claims?.length > 0 && (
        <div className="verification-section">
          <div className="verification-section-title" style={{ color: '#ef4444' }}>
            ⚠ Unverified Claims ({ungrounded_claims.length})
          </div>
          <div className="claim-list">
            {ungrounded_claims.map((c, i) => (
              <span key={i} className="claim-tag ungrounded">{c}</span>
            ))}
          </div>
          <div className="verification-note">
            These values were not found in the raw tool data. Review before acting.
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Main ReasoningPanel ───────────────────────────────────────────────────── */
export default function ReasoningPanel({
  reasoningSteps,
  toolInvocations,
  agentStates,
  tokenUsage,
  verificationResult,
  modelName,
}) {
  const [activeTab, setActiveTab] = useState('reasoning')
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [reasoningSteps, toolInvocations, activeTab])

  const tabs = [
    { id: 'reasoning', label: 'Reasoning', icon: Brain },
    { id: 'tools', label: 'Tool Calls', icon: Wrench },
    { id: 'lifecycle', label: 'Timeline', icon: Activity },
    { id: 'verification', label: 'Verification', icon: ShieldCheck },
  ]

  return (
    <div className="panel panel-reasoning">
      <div className="panel-header">
        <Brain size={16} className="panel-header-icon" />
        <h2>Reasoning Console</h2>
      </div>

      <div className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon size={12} style={{ marginRight: 4, verticalAlign: 'middle' }} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="panel-content" ref={scrollRef}>

        {/* ── Reasoning Tab ─────────────────────────────────────────────── */}
        {activeTab === 'reasoning' && (
          <div className="reasoning-section">
            {reasoningSteps.length === 0 ? (
              <div className="empty-state">
                <Brain size={24} color="var(--text-muted)" />
                <p className="empty-state-text">
                  Agent reasoning will appear here<br />as the system processes your query.
                </p>
              </div>
            ) : (
              reasoningSteps.map((step, i) => (
                <div key={i} className="reasoning-step">
                  <div className="reasoning-step-agent">{step.agent}</div>
                  <div className="reasoning-step-thought">{step.thought}</div>
                  <div className="reasoning-step-action">{step.action}</div>
                </div>
              ))
            )}
          </div>
        )}

        {/* ── Tool Calls Tab ─────────────────────────────────────────────── */}
        {activeTab === 'tools' && (
          <div className="reasoning-section">
            {toolInvocations.length === 0 ? (
              <div className="empty-state">
                <Wrench size={24} color="var(--text-muted)" />
                <p className="empty-state-text">
                  Tool invocations will appear here<br />with parameters and execution times.
                </p>
              </div>
            ) : (
              toolInvocations.map((tool, i) => (
                <div key={i} className="tool-invocation">
                  <div className="tool-name">
                    <span>{tool.tool_name}()</span>
                    <span className="tool-latency">{tool.execution_time_ms?.toFixed(1)}ms</span>
                  </div>
                  <div className="tool-agent">Agent: {tool.agent}</div>
                  {tool.parameters && Object.keys(tool.parameters).length > 0 && (
                    <div className="tool-params">
                      Input: {JSON.stringify(tool.parameters, null, 2)}
                    </div>
                  )}
                  {tool.output && (
                    <details>
                      <summary className="tool-output-toggle">View Output</summary>
                      <div className="tool-params" style={{ borderLeft: '2px solid var(--accent-green)', marginTop: 4 }}>
                        {typeof tool.output === 'string'
                          ? tool.output
                          : JSON.stringify(tool.output, null, 2).substring(0, 600)}
                        {JSON.stringify(tool.output || '').length > 600 ? '\n...[truncated]' : ''}
                      </div>
                    </details>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* ── Timeline / Gantt Tab ───────────────────────────────────────── */}
        {activeTab === 'lifecycle' && (
          <div className="reasoning-section">
            <GanttTimeline agentStates={agentStates} />
          </div>
        )}

        {/* ── Verification Tab ───────────────────────────────────────────── */}
        {activeTab === 'verification' && (
          <div className="reasoning-section">
            <VerificationTab verificationResult={verificationResult} />
          </div>
        )}

      </div>

      {/* ── Token Monitor ──────────────────────────────────────────────────── */}
      <div className="token-monitor">
        <div className="token-stat">
          <span className="token-stat-label">Model</span>
          <span className="token-stat-value" style={{ fontSize: 10 }}>
            {modelName || 'llama-3.3-70b'}
          </span>
        </div>
        <div className="token-stat">
          <span className="token-stat-label">Prompt</span>
          <span className="token-stat-value">{tokenUsage.promptTokens || 0}</span>
        </div>
        <div className="token-stat">
          <span className="token-stat-label">Completion</span>
          <span className="token-stat-value green">{tokenUsage.completionTokens || 0}</span>
        </div>
        <div className="token-stat">
          <span className="token-stat-label">Tool Calls</span>
          <span className="token-stat-value purple">{tokenUsage.toolCalls || 0}</span>
        </div>
        <div className="token-stat">
          <span className="token-stat-label">Total Time</span>
          <span className="token-stat-value orange">
            {tokenUsage.totalTime ? `${(tokenUsage.totalTime / 1000).toFixed(1)}s` : '—'}
          </span>
        </div>
      </div>
    </div>
  )
}
