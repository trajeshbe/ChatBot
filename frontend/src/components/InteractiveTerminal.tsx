/**
 * Interactive Terminal Component
 *
 * Full-featured terminal emulator using xterm.js with bidirectional WebSocket communication.
 * Enables interactive sessions with Claude CLI where user can type responses to prompts.
 *
 * Features:
 * - Real-time terminal I/O via WebSocket
 * - Keyboard input forwarding to backend
 * - Auto-resize with container
 * - Copy/paste support
 * - Terminal history
 */

import { useEffect, useRef, useState } from 'react'
import { Terminal as TerminalIcon, Maximize2, Minimize2 } from 'lucide-react'

// Import xterm and addons
// These will be imported dynamically to avoid SSR issues with Next.js
let Terminal: any = null
let FitAddon: any = null
let WebLinksAddon: any = null

interface InteractiveTerminalProps {
  taskId: string
  onClose?: () => void
}

export default function InteractiveTerminal({ taskId, onClose }: InteractiveTerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null)
  const xtermRef = useRef<any>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const fitAddonRef = useRef<any>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [hasError, setHasError] = useState(false)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    // Dynamically import xterm to avoid SSR issues
    const loadXterm = async () => {
      if (typeof window === 'undefined') return

      try {
        const xtermModule = await import('@xterm/xterm')
        const fitAddonModule = await import('@xterm/addon-fit')
        const webLinksAddonModule = await import('@xterm/addon-web-links')

        Terminal = xtermModule.Terminal
        FitAddon = fitAddonModule.FitAddon
        WebLinksAddon = webLinksAddonModule.WebLinksAddon

        initTerminal()
      } catch (error) {
        console.error('Failed to load xterm:', error)
        setHasError(true)
      }
    }

    loadXterm()

    return () => {
      cleanup()
    }
  }, [taskId])

  const initTerminal = () => {
    if (!terminalRef.current || !Terminal) return

    // Create terminal instance
    const term = new Terminal({
      cursorBlink: true,
      cursorStyle: 'block',  // ✅ FIX: Visible block cursor
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      scrollback: 10000,  // ✅ FIX: Large scrollback buffer for scrolling
      rows: 24,  // ✅ FIX: Initial terminal size
      cols: 80,
      convertEol: true,  // ✅ FIX: Convert \n to \r\n for proper line breaks
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#ffffff',
        cursorAccent: '#000000',  // ✅ FIX: Cursor accent color
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#e5e5e5'
      },
      allowProposedApi: true
    })

    // Add addons
    const fitAddon = new FitAddon()
    const webLinksAddon = new WebLinksAddon()

    term.loadAddon(fitAddon)
    term.loadAddon(webLinksAddon)

    // Open terminal in DOM
    term.open(terminalRef.current)

    // Fit to container
    fitAddon.fit()

    // Store refs
    xtermRef.current = term
    fitAddonRef.current = fitAddon

    // Connect WebSocket
    connectWebSocket(term)

    // Handle keyboard input
    term.onData((data: string) => {
      // Send user input to backend via WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'terminal_input',
          data: data
        }))
      }
    })

    // Handle window resize
    const handleResize = () => {
      fitAddon.fit()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }

  const connectWebSocket = (term: any) => {
    const wsUrl = `${API_URL.replace('http', 'ws')}/api/v1/agent/tasks/${taskId}/terminal`

    console.log('🔌 Connecting to terminal WebSocket:', wsUrl)

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('✅ Terminal WebSocket connected')
      setIsConnected(true)
      setHasError(false)
      term.write('\r\n\x1b[32m● Connected to terminal session\x1b[0m\r\n\r\n')
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)

        if (message.type === 'terminal_output') {
          // Write output to terminal
          term.write(message.data)
        } else if (message.type === 'error') {
          term.write(`\r\n\x1b[31m✗ Error: ${message.error}\x1b[0m\r\n`)
        } else if (message.type === 'disconnected') {
          term.write('\r\n\x1b[33m● Session ended\x1b[0m\r\n')
          setIsConnected(false)
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('❌ Terminal WebSocket error:', error)
      setHasError(true)
      term.write('\r\n\x1b[31m✗ Connection error\x1b[0m\r\n')
    }

    ws.onclose = () => {
      console.log('🔌 Terminal WebSocket closed')
      setIsConnected(false)
      term.write('\r\n\x1b[33m● Connection closed\x1b[0m\r\n')
    }

    wsRef.current = ws
  }

  const cleanup = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    if (xtermRef.current) {
      xtermRef.current.dispose()
      xtermRef.current = null
    }
  }

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
    // Refit terminal after fullscreen toggle
    setTimeout(() => {
      if (fitAddonRef.current) {
        fitAddonRef.current.fit()
      }
    }, 100)
  }

  return (
    <div className={`bg-slate-900 rounded-lg border border-slate-700 ${
      isFullscreen ? 'fixed inset-4 z-50' : 'relative'
    }`}>
      {/* Terminal Header */}
      <div className="bg-slate-800 px-4 py-2 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TerminalIcon className="w-4 h-4 text-green-400" />
          <span className="text-sm font-medium text-slate-200">
            Interactive Terminal
          </span>
          {isConnected && (
            <span className="flex items-center gap-1 text-xs text-green-400">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              Connected
            </span>
          )}
          {hasError && (
            <span className="flex items-center gap-1 text-xs text-red-400">
              <span className="w-2 h-2 bg-red-400 rounded-full"></span>
              Error
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleFullscreen}
            className="text-slate-400 hover:text-slate-200 transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-red-400 transition-colors text-sm"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Terminal Container */}
      <div
        ref={terminalRef}
        className={`${
          isFullscreen ? 'h-[calc(100vh-8rem)]' : 'h-96'
        } p-2 overflow-auto`}
        style={{ backgroundColor: '#1e1e1e' }}
      />

      {/* Terminal Footer */}
      <div className="bg-slate-800 px-4 py-2 border-t border-slate-700 flex items-center justify-between">
        <div className="text-xs text-slate-400">
          Task ID: {taskId}
        </div>
        <div className="text-xs text-slate-400">
          Press Ctrl+C to interrupt • Type to interact
        </div>
      </div>
    </div>
  )
}
