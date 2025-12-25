"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

// Types
export interface AgentTask {
  id: string
  name: string
  prompt_text?: string
  user_id: string
  created_at?: string
}

export interface AgentColumn {
  id: string
  title: string
  subtitle: string
  agents: AgentTask[]
}

export interface AgentKanbanProps {
  columns: AgentColumn[]
  onColumnsChange?: (columns: AgentColumn[]) => void
  onAgentMove?: (agentId: string, fromColumnId: string, toColumnId: string) => void
  onAgentEdit?: (agentId: string) => void
  onAgentDelete?: (agentId: string) => void
  className?: string
}

export function AgentKanbanBoard({
  columns: initialColumns,
  onColumnsChange,
  onAgentMove,
  onAgentEdit,
  onAgentDelete,
  className,
}: AgentKanbanProps) {
  const [columns, setColumns] = React.useState<AgentColumn[]>(initialColumns)
  const [draggedAgent, setDraggedAgent] = React.useState<{
    agent: AgentTask
    sourceColumnId: string
  } | null>(null)
  const [dropTarget, setDropTarget] = React.useState<string | null>(null)

  // Update columns when props change
  React.useEffect(() => {
    setColumns(initialColumns)
  }, [initialColumns])

  const handleDragStart = (agent: AgentTask, columnId: string) => {
    setDraggedAgent({ agent, sourceColumnId: columnId })
  }

  const handleDragOver = (e: React.DragEvent, columnId: string) => {
    e.preventDefault()
    setDropTarget(columnId)
  }

  const handleDrop = (targetColumnId: string) => {
    if (!draggedAgent || draggedAgent.sourceColumnId === targetColumnId) {
      setDraggedAgent(null)
      setDropTarget(null)
      return
    }

    const newColumns = columns.map((col) => {
      if (col.id === draggedAgent.sourceColumnId) {
        return { ...col, agents: col.agents.filter((a) => a.id !== draggedAgent.agent.id) }
      }
      if (col.id === targetColumnId) {
        return { ...col, agents: [...col.agents, draggedAgent.agent] }
      }
      return col
    })

    setColumns(newColumns)
    onColumnsChange?.(newColumns)
    onAgentMove?.(draggedAgent.agent.id, draggedAgent.sourceColumnId, targetColumnId)
    setDraggedAgent(null)
    setDropTarget(null)
  }

  return (
    <div className={cn("flex gap-4 overflow-x-auto pb-4", className)}>
      {columns.map((column) => {
        const isDropActive = dropTarget === column.id && draggedAgent?.sourceColumnId !== column.id
        const isActive = column.id === "active"

        return (
          <div
            key={column.id}
            onDragOver={(e) => handleDragOver(e, column.id)}
            onDrop={() => handleDrop(column.id)}
            onDragLeave={() => setDropTarget(null)}
            className={cn(
              "min-w-[320px] max-w-[320px] rounded-xl p-4 transition-all duration-200",
              "bg-lighter border-2",
              isDropActive ? "border-primary/50 border-dashed bg-primary/5" : "border-transparent",
            )}
          >
            {/* Column Header */}
            <div className="mb-4 px-1">
              <div className="flex items-center gap-2 mb-1">
                <div className={cn("h-3 w-3 rounded-full", isActive ? "bg-green-500" : "bg-gray-500")} />
                <h2 className="text-lg font-semibold text-text">{column.title}</h2>
                <span className="rounded-full bg-darker px-2.5 py-0.5 text-xs font-medium text-text-secondary">
                  {column.agents.length}
                </span>
              </div>
              <p className="text-xs text-text-secondary ml-5">{column.subtitle}</p>
            </div>

            {/* Agents */}
            <div className="flex min-h-[200px] flex-col gap-3">
              {column.agents.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-text-secondary text-sm">
                  {isActive ? "No active agents" : "No deactivated agents"}
                </div>
              ) : (
                column.agents.map((agent) => {
                  const isDragging = draggedAgent?.agent.id === agent.id

                  return (
                    <div
                      key={agent.id}
                      draggable
                      onDragStart={() => handleDragStart(agent, column.id)}
                      onDragEnd={() => setDraggedAgent(null)}
                      className={cn(
                        "cursor-grab rounded-lg border border-border bg-darker p-4 shadow-sm transition-all duration-150",
                        "hover:-translate-y-0.5 hover:shadow-md hover:border-primary/30 active:cursor-grabbing",
                        isDragging && "rotate-2 opacity-50",
                        !isActive && "opacity-60"
                      )}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className={cn(
                          "text-sm font-semibold flex-1",
                          isActive ? "text-text" : "text-text-secondary"
                        )}>
                          {agent.name}
                        </h3>
                        <span className={cn(
                          "text-[10px] font-medium uppercase px-2 py-0.5 rounded",
                          isActive ? "bg-green-500/20 text-green-400" : "bg-gray-500/20 text-gray-400"
                        )}>
                          {isActive ? "Active" : "Deactivated"}
                        </span>
                      </div>

                      {agent.prompt_text && (
                        <p className="text-xs text-text-secondary mb-3 line-clamp-2">
                          {agent.prompt_text.substring(0, 100)}...
                        </p>
                      )}

                      <div className="flex gap-2 pt-2 border-t border-border">
                        <button
                          onClick={() => onAgentEdit?.(agent.id)}
                          className="flex-1 px-3 py-1.5 text-xs font-medium rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => onAgentDelete?.(agent.id)}
                          className="px-3 py-1.5 text-xs font-medium rounded bg-red-600/10 text-red-400 hover:bg-red-600/20 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  )
                })
              )}
            </div>

            {/* Drag instruction */}
            {column.agents.length > 0 && (
              <div className="mt-4 text-center text-xs text-text-secondary/60">
                Drag agents to {isActive ? "deactivate" : "activate"}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
