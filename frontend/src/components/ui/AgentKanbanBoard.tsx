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

  // Helper to extract a clean description from the full prompt
  const getAgentDescription = (prompt: string | undefined): string => {
    if (!prompt) return "No description available";
    
    // Extract the first line which usually has "You are [name], an AI-powered..."
    const lines = prompt.split('\n');
    const firstLine = lines[0]?.trim();
    
    if (firstLine && firstLine.startsWith('You are')) {
      return firstLine;
    }
    
    // Fallback: try to find business description
    const businessDescIndex = lines.findIndex(line => line.includes('What we do:'));
    if (businessDescIndex !== -1 && lines[businessDescIndex + 1]) {
      return lines[businessDescIndex + 1].trim();
    }
    
    // Last resort: return first meaningful line
    return lines.find(line => line.trim().length > 20)?.trim() || "Professional AI voice assistant";
  }

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
    <div className={cn("grid grid-cols-1 lg:grid-cols-2 gap-6", className)}>
      {columns.map((column) => {
        const isDropActive = dropTarget === column.id && draggedAgent?.sourceColumnId !== column.id
        const isActive = column.id === "active"

        return (
          <div
            key={column.id}
            className={cn(
              "flex flex-col rounded-xl transition-all duration-300",
              "bg-lighter/50 backdrop-blur-sm",
              "border-2 shadow-lg",
              isDropActive 
                ? "border-primary/70 shadow-primary/20 ring-4 ring-primary/10 scale-[1.02]" 
                : "border-border hover:border-border/60"
            )}
          >
            {/* Column Header */}
            <div className="px-6 py-5 border-b border-border/50 bg-gradient-to-b from-lighter/80 to-transparent rounded-t-xl">
              <div className="flex items-center gap-3 mb-2">
                <div className={cn(
                  "h-3 w-3 rounded-full shadow-lg transition-all duration-300",
                  isActive ? "bg-green-500 shadow-green-500/50" : "bg-gray-500 shadow-gray-500/30"
                )} />
                <h2 className="text-xl font-bold text-text">{column.title}</h2>
                <span className="ml-auto rounded-full bg-darker/80 px-3 py-1 text-sm font-semibold text-text-secondary border border-border/30">
                  {column.agents.length}
                </span>
              </div>
              <p className="text-sm text-text-secondary/80 ml-6">{column.subtitle}</p>
            </div>

            {/* Drop Zone Area */}
            <div
              onDragOver={(e) => handleDragOver(e, column.id)}
              onDrop={() => handleDrop(column.id)}
              onDragLeave={() => setDropTarget(null)}
              className={cn(
                "flex-1 p-6 min-h-[400px] transition-all duration-300",
                isDropActive && "bg-primary/5"
              )}
            >
              {/* Agents */}
              <div className="flex flex-col gap-3">
                {column.agents.length === 0 ? (
                  <div className={cn(
                    "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 min-h-[300px] transition-all",
                    isDropActive 
                      ? "border-primary/50 bg-primary/5" 
                      : "border-border/30 bg-darker/30"
                  )}>
                    <div className={cn(
                      "w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-all",
                      isActive ? "bg-green-500/10" : "bg-gray-500/10"
                    )}>
                      <div className={cn(
                        "w-8 h-8 rounded-full",
                        isActive ? "bg-green-500/20" : "bg-gray-500/20"
                      )} />
                    </div>
                    <p className="text-text-secondary/60 text-sm font-medium mb-1">
                      {isActive ? "No active agents yet" : "No deactivated agents"}
                    </p>
                    <p className="text-text-secondary/40 text-xs text-center max-w-[200px]">
                      {isDropActive 
                        ? "Drop here to " + (isActive ? "activate" : "deactivate")
                        : "Drag agents here to " + (isActive ? "activate them" : "deactivate them")
                      }
                    </p>
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
                          "cursor-grab rounded-lg border bg-darker p-4 shadow-sm transition-all duration-200",
                          "hover:-translate-y-1 hover:shadow-lg hover:border-primary/40 active:cursor-grabbing",
                          isDragging && "rotate-3 opacity-40 scale-95",
                          !isActive && "opacity-70",
                          isActive ? "border-border/50" : "border-border/30"
                        )}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className={cn(
                            "text-sm font-semibold flex-1 pr-2",
                            isActive ? "text-text" : "text-text-secondary"
                          )}>
                            {agent.name}
                          </h3>
                          <span className={cn(
                            "text-[10px] font-bold uppercase px-2 py-1 rounded whitespace-nowrap",
                            isActive 
                              ? "bg-green-500/20 text-green-400 border border-green-500/30" 
                              : "bg-gray-500/20 text-gray-400 border border-gray-500/20"
                          )}>
                            {isActive ? "Active" : "Deactivated"}
                          </span>
                        </div>

                        <p className="text-xs text-text-secondary/80 mb-3 line-clamp-2 leading-relaxed">
                          {getAgentDescription(agent.prompt_text)}
                        </p>

                        <div className="flex gap-2 pt-3 border-t border-border/30">
                          <button
                            onClick={() => onAgentEdit?.(agent.id)}
                            className="flex-1 px-3 py-2 text-xs font-semibold rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-all hover:shadow-md active:scale-95"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => onAgentDelete?.(agent.id)}
                            className="px-3 py-2 text-xs font-semibold rounded-md bg-red-600/10 text-red-400 hover:bg-red-600/20 border border-red-600/20 hover:border-red-600/40 transition-all active:scale-95"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>

              {/* Drop Zone Hint - Show when dragging */}
              {draggedAgent && column.agents.length > 0 && (
                <div className={cn(
                  "mt-4 p-4 rounded-lg border-2 border-dashed text-center transition-all duration-300",
                  isDropActive 
                    ? "border-primary/60 bg-primary/10 text-primary" 
                    : "border-border/20 bg-darker/20 text-text-secondary/50"
                )}>
                  <p className="text-xs font-medium">
                    Drop here to {isActive ? "activate" : "deactivate"}
                  </p>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
