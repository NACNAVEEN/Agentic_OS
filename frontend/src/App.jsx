import { useState, useRef, useCallback, useEffect } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import ConversationPanel from './components/ConversationPanel'
import AgentGraph from './components/AgentGraph'
import ReasoningPanel from './components/ReasoningPanel'

const WS_URL = 'ws://localhost:8000/ws/agent'
const API_URL = 'http://localhost:8000'

const AGENT_DISPLAY_NAMES = {
  planner: 'Planner Agent',
  asset_agent: 'Asset Agent',
  alarm_agent: 'Alarm Agent',
  energy_agent: 'Energy Agent',
  documentation_agent: 'Documentation Agent',
  supervisor: 'Supervisor Agent',
  verification: 'Verification Agent',
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [agentStates, setAgentStates] = useState({})
  const [spawnedAgents, setSpawnedAgents] = useState([])
  const [reasoningSteps, setReasoningSteps] = useState([])
  const [toolInvocations, setToolInvocations] = useState([])
  const [tokenUsage, setTokenUsage] = useState({})
  const [executionPlan, setExecutionPlan] = useState(null)
  const [verificationResult, setVerificationResult] = useState(null)
  const [modelName, setModelName] = useState('llama-3.3-70b')
  const [sessionId] = useState(() => crypto.randomUUID())

  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  // ── Fetch live model name from /api/health on mount ────────────────────
  useEffect(() => {
    fetch(`${API_URL}/api/health`)
      .then(r => r.json())
      .then(data => {
        if (data.model) setModelName(data.model)
      })
      .catch(() => { }) // silently fail — defaults to hardcoded fallback
  }, [])

  // ── WebSocket connection ────────────────────────────────────────────────
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      setIsConnected(true)
      console.log('🔌 Connected to AgenticOS backend')
    }

    ws.onclose = () => {
      setIsConnected(false)
      console.log('🔌 Disconnected. Reconnecting in 3s...')
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000)
    }

    ws.onerror = (err) => console.error('WebSocket error:', err)

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      handleWSMessage(msg)
    }

    wsRef.current = ws
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    connectWebSocket()
    return () => {
      clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [connectWebSocket])

  // ── WebSocket message handler ──────────────────────────────────────────
  const handleWSMessage = useCallback((msg) => {
    switch (msg.type) {

      case 'query_received':
        setAgentStates(prev => ({
          ...prev,
          planner: { status: 'running', displayName: 'Planner Agent', executionTime: 0 }
        }))
        break

      case 'planner_complete': {
        const spawned = msg.data.agents_to_spawn || []
        setExecutionPlan(msg.data.plan || null)
        setSpawnedAgents(spawned)
        setAgentStates(prev => {
          const next = { ...prev, planner: { ...prev.planner, status: 'completed' } }
          spawned.forEach(agent => {
            next[agent] = {
              status: 'running',
              displayName: AGENT_DISPLAY_NAMES[agent] || agent,
              executionTime: 0,
            }
          })
          return next
        })
        break
      }

      case 'agent_spawned':
        // Already handled in planner_complete
        break

      case 'reasoning_step':
        setReasoningSteps(prev => [...prev, msg.data])
        break

      case 'tool_invocation':
        setToolInvocations(prev => [...prev, msg.data])
        break

      case 'agent_complete':
        setAgentStates(prev => ({
          ...prev,
          [msg.data.agent]: {
            ...prev[msg.data.agent],
            status: 'completed',
            executionTime: msg.data.execution_time_ms || 0,
            toolsUsed: msg.data.tools_used || [],
            confidenceScore: msg.data.confidence_score ?? 1.0,
          }
        }))
        break

      case 'verification_complete':
        setVerificationResult(msg.data)
        setAgentStates(prev => ({
          ...prev,
          verification: {
            status: 'completed',
            displayName: 'Verification Agent',
            executionTime: 0,
          }
        }))
        break

      case 'final_response':
        setAgentStates(prev => ({
          ...prev,
          supervisor: {
            status: 'completed',
            displayName: 'Supervisor Agent',
            executionTime: msg.data.total_execution_time_ms || 0,
          }
        }))
        // Also capture verification if it came with final_response
        if (msg.data.verification_result?.status) {
          setVerificationResult(msg.data.verification_result)
        }
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: msg.data.response,
        }])
        setTokenUsage({
          promptTokens: msg.data.token_usage?.prompt_tokens || 0,
          completionTokens: msg.data.token_usage?.completion_tokens || 0,
          toolCalls: msg.data.token_usage?.tool_calls || 0,
          totalTime: msg.data.total_execution_time_ms || 0,
        })
        setIsProcessing(false)
        break

      case 'error':
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `❌ Error: ${msg.data}`,
        }])
        setIsProcessing(false)
        break

      default:
        break
    }
  }, [])

  // ── Send query ─────────────────────────────────────────────────────────
  const handleSend = useCallback((query) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Not connected to backend. Please ensure the server is running on port 8000.',
      }])
      return
    }

    // Reset state for new query
    setIsProcessing(true)
    setAgentStates({})
    setSpawnedAgents([])
    setReasoningSteps([])
    setToolInvocations([])
    setTokenUsage({})
    setExecutionPlan(null)
    setVerificationResult(null)

    setMessages(prev => [...prev, { role: 'user', content: query }])
    wsRef.current.send(JSON.stringify({ query, session_id: sessionId }))
  }, [sessionId])

  return (
    <div className="app-container">
      {/* ── Header ────────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="app-logo">
          <div className="app-logo-icon">A</div>
          <div>
            <h1>AgenticOS</h1>
            <span>Multi-Agent Operations Intelligence</span>
          </div>
        </div>
        <div className="header-status">
          <div className="model-badge">{modelName}</div>
          <div className="status-indicator">
            <div className={`status-dot ${isConnected ? '' : 'disconnected'}`} />
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </header>

      {/* ── Main 3-Panel Layout ────────────────────────────────────────── */}
      <main className="app-main">
        <ConversationPanel
          messages={messages}
          onSend={handleSend}
          isProcessing={isProcessing}
        />

        <ReactFlowProvider>
          <AgentGraph
            agentStates={agentStates}
            spawnedAgents={spawnedAgents}
          />
        </ReactFlowProvider>

        <ReasoningPanel
          reasoningSteps={reasoningSteps}
          toolInvocations={toolInvocations}
          agentStates={agentStates}
          tokenUsage={tokenUsage}
          verificationResult={verificationResult}
          modelName={modelName}
        />
      </main>
    </div>
  )
}
