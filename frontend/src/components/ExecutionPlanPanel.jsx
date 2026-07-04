import { CheckCircle, Clock, Layers } from 'lucide-react'

const AGENT_ICONS = {
  asset_agent: '🏗️',
  alarm_agent: '🚨',
  energy_agent: '⚡',
  documentation_agent: '📄',
  planner: '🧠',
  supervisor: '👔',
  verification: '🔍',
}

const AGENT_LABELS = {
  asset_agent: 'Asset Agent',
  alarm_agent: 'Alarm Agent',
  energy_agent: 'Energy Agent',
  documentation_agent: 'Documentation Agent',
}

export default function ExecutionPlanPanel({ plan, agentStates }) {
  if (!plan || !plan.execution_plan || plan.execution_plan.length === 0) return null

  return (
    <div className="execution-plan-panel">
      <div className="plan-header">
        <Layers size={14} style={{ marginRight: 6, color: 'var(--accent-cyan)' }} />
        <span className="plan-title">Execution Plan</span>
        <span className="plan-badge">{plan.agents_to_spawn?.length || 0} agents</span>
      </div>

      {plan.understanding && (
        <div className="plan-understanding">
          <span className="plan-understanding-label">Intent: </span>
          {plan.understanding}
        </div>
      )}

      <div className="plan-steps">
        {plan.execution_plan.map((step) => {
          const agentKey = step.agent
          const agentState = agentStates?.[agentKey]
          const status = agentState?.status || 'pending'
          return (
            <div key={step.step} className={`plan-step plan-step-${status}`}>
              <div className="plan-step-num">{step.step}</div>
              <div className="plan-step-body">
                <div className="plan-step-agent">
                  <span className="plan-step-icon">{AGENT_ICONS[agentKey] || '🤖'}</span>
                  {AGENT_LABELS[agentKey] || agentKey}
                </div>
                <div className="plan-step-task">{step.task}</div>
              </div>
              <div className="plan-step-status">
                {status === 'completed' ? (
                  <CheckCircle size={14} color="var(--accent-green)" />
                ) : status === 'running' ? (
                  <Clock size={14} color="var(--accent-cyan)" style={{ animation: 'spin 1s linear infinite' }} />
                ) : (
                  <div className="plan-step-dot" />
                )}
              </div>
            </div>
          )
        })}
      </div>

      {plan.reasoning && (
        <div className="plan-reasoning">
          <span className="plan-reasoning-label">Planner reasoning: </span>
          {plan.reasoning}
        </div>
      )}
    </div>
  )
}
