import { useMemo, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { GitBranch, Network } from 'lucide-react'

/* Custom node component */
function AgentNodeComponent({ data }) {
  const statusClass = `agent-node status-${data.status || 'idle'}`
  return (
    <div className={statusClass}>
      <div className="agent-node-label">{data.label}</div>
      <div className={`agent-node-status ${data.status || 'idle'}`}>
        {data.status === 'idle' ? '● Standby' :
         data.status === 'created' ? '◉ Created' :
         data.status === 'running' ? '▶ Running' :
         data.status === 'completed' ? '✓ Completed' :
         data.status === 'failed' ? '✗ Failed' : '● Idle'}
      </div>
      {data.executionTime > 0 && (
        <div className="agent-node-time">{data.executionTime.toFixed(0)}ms</div>
      )}
    </div>
  )
}

const nodeTypes = { agentNode: AgentNodeComponent }

/* Default graph layout */
const DEFAULT_NODES = [
  { id: 'planner', type: 'agentNode', position: { x: 250, y: 20 }, data: { label: '🧠 Planner Agent', status: 'idle', executionTime: 0 } },
  { id: 'asset_agent', type: 'agentNode', position: { x: 50, y: 180 }, data: { label: '🏗️ Asset Agent', status: 'idle', executionTime: 0 } },
  { id: 'alarm_agent', type: 'agentNode', position: { x: 230, y: 180 }, data: { label: '🚨 Alarm Agent', status: 'idle', executionTime: 0 } },
  { id: 'energy_agent', type: 'agentNode', position: { x: 410, y: 180 }, data: { label: '⚡ Energy Agent', status: 'idle', executionTime: 0 } },
  { id: 'documentation_agent', type: 'agentNode', position: { x: 590, y: 180 }, data: { label: '📄 Docs Agent', status: 'idle', executionTime: 0 } },
  { id: 'supervisor', type: 'agentNode', position: { x: 250, y: 340 }, data: { label: '👔 Supervisor Agent', status: 'idle', executionTime: 0 } },
]

const DEFAULT_EDGES = [
  { id: 'e-planner-asset', source: 'planner', target: 'asset_agent', animated: false, style: { stroke: 'rgba(255,255,255,0.1)' } },
  { id: 'e-planner-alarm', source: 'planner', target: 'alarm_agent', animated: false, style: { stroke: 'rgba(255,255,255,0.1)' } },
  { id: 'e-planner-energy', source: 'planner', target: 'energy_agent', animated: false, style: { stroke: 'rgba(255,255,255,0.1)' } },
  { id: 'e-planner-docs', source: 'planner', target: 'documentation_agent', animated: false, style: { stroke: 'rgba(255,255,255,0.1)' } },
  { id: 'e-asset-supervisor', source: 'asset_agent', target: 'supervisor', animated: false, style: { stroke: 'rgba(255,255,255,0.1)' } },
  { id: 'e-alarm-supervisor', source: 'alarm_agent', target: 'supervisor', animated: false, style: { stroke: 'rgba(255,255,255,0.1)' } },
  { id: 'e-energy-supervisor', source: 'energy_agent', target: 'supervisor', animated: false, style: { stroke: 'rgba(255,255,255,0.1)' } },
  { id: 'e-docs-supervisor', source: 'documentation_agent', target: 'supervisor', animated: false, style: { stroke: 'rgba(255,255,255,0.1)' } },
]

export default function AgentGraph({ agentStates, spawnedAgents }) {
  const nodes = useMemo(() => {
    return DEFAULT_NODES.map(node => {
      const agentState = agentStates[node.id]
      const isSpawned = spawnedAgents.includes(node.id)
      let status = 'idle'
      let executionTime = 0

      if (agentState) {
        status = agentState.status
        executionTime = agentState.executionTime || 0
      } else if (node.id === 'planner' || node.id === 'supervisor') {
        // Planner/Supervisor always show if they have a state
        if (agentStates[node.id]) {
          status = agentStates[node.id].status
        }
      } else if (!isSpawned) {
        status = 'idle'
      }

      return {
        ...node,
        data: { ...node.data, status, executionTime }
      }
    })
  }, [agentStates, spawnedAgents])

  const edges = useMemo(() => {
    return DEFAULT_EDGES.map(edge => {
      const sourceState = agentStates[edge.source]
      const targetIsSpawned = spawnedAgents.includes(edge.target) || 
                               edge.target === 'supervisor' ||
                               edge.source === 'planner'
      
      const isActive = sourceState && 
                       (sourceState.status === 'running' || sourceState.status === 'completed') &&
                       targetIsSpawned

      return {
        ...edge,
        animated: isActive,
        style: {
          stroke: isActive ? 'rgba(0, 212, 255, 0.6)' : 'rgba(255,255,255,0.06)',
          strokeWidth: isActive ? 2 : 1,
        }
      }
    })
  }, [agentStates, spawnedAgents])

  return (
    <div className="panel panel-graph">
      <div className="panel-header">
        <Network size={16} className="panel-header-icon" />
        <h2>Agent Execution Graph</h2>
        {spawnedAgents.length > 0 && (
          <span className="badge badge-info" style={{ marginLeft: 'auto' }}>
            {spawnedAgents.length} agents spawned
          </span>
        )}
      </div>
      <div className="panel-content" style={{ padding: 0 }}>
        <div className="agent-graph-container">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
            panOnDrag={true}
            zoomOnScroll={true}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="rgba(255,255,255,0.03)" gap={20} />
            <Controls 
              showInteractive={false}
              style={{ 
                background: 'var(--bg-card)', 
                border: '1px solid var(--glass-border)',
                borderRadius: 'var(--radius-sm)'
              }}
            />
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}
