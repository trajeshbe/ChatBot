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
import { Terminal as TerminalIcon, Maximize2, Minimize2, Clipboard } from 'lucide-react'

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
  const isInitializedRef = useRef<boolean>(false)  // ✅ Track initialization state
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [hasError, setHasError] = useState(false)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    // ✅ Prevent duplicate initialization (React Strict Mode runs effects twice)
    if (isInitializedRef.current) {
      console.log('⚠️ Terminal already initialized, skipping duplicate initialization')
      return
    }

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

        // ✅ Mark as initialized before initializing terminal
        isInitializedRef.current = true
        initTerminal()
      } catch (error) {
        console.error('Failed to load xterm:', error)
        setHasError(true)
      }
    }

    loadXterm()

    return () => {
      // ✅ Reset initialization flag on cleanup
      isInitializedRef.current = false
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

    // ✅ IMPROVED: Handle paste with multiple approaches for browser compatibility
    const handlePaste = async (event: ClipboardEvent) => {
      try {
        event.preventDefault()
        event.stopPropagation()

        let text: string | null = null

        // Method 1: Try event.clipboardData (most common)
        if (event.clipboardData) {
          text = event.clipboardData.getData('text')
          console.log('📋 Paste via clipboardData:', text?.length, 'chars')
        }

        // Method 2: Try navigator.clipboard API (fallback)
        if (!text && navigator.clipboard && navigator.clipboard.readText) {
          try {
            text = await navigator.clipboard.readText()
            console.log('📋 Paste via navigator.clipboard:', text?.length, 'chars')
          } catch (err) {
            console.warn('Clipboard API denied:', err)
          }
        }

        // Send to backend if we got text
        if (text && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          console.log(`✅ Sending ${text.length} characters to terminal`)
          wsRef.current.send(JSON.stringify({
            type: 'terminal_input',
            data: text
          }))
        } else {
          console.error('❌ No text found in clipboard or WebSocket not connected')
        }
      } catch (error) {
        console.error('❌ Paste error:', error)
      }
    }

    // Attach paste listener to terminal container AND document
    const terminalElement = terminalRef.current
    if (terminalElement) {
      // On the terminal element itself
      terminalElement.addEventListener('paste', handlePaste as EventListener)

      // Also listen for paste when terminal is focused
      terminalElement.addEventListener('keydown', async (e: KeyboardEvent) => {
        // Ctrl+V or Cmd+V
        if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
          e.preventDefault()
          console.log('📋 Keyboard paste detected (Ctrl/Cmd+V)')

          try {
            if (navigator.clipboard && navigator.clipboard.readText) {
              const text = await navigator.clipboard.readText()
              if (text && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                console.log(`✅ Pasting ${text.length} characters`)
                wsRef.current.send(JSON.stringify({
                  type: 'terminal_input',
                  data: text
                }))
              }
            }
          } catch (err) {
            console.error('❌ Clipboard read failed:', err)
            alert('Paste permission denied. Please use right-click → Paste or grant clipboard access.')
          }
        }
      })
    }

    // Handle window resize
    const handleResize = () => {
      fitAddon.fit()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (terminalElement) {
        terminalElement.removeEventListener('paste', handlePaste as EventListener)
        // Note: keydown listener doesn't need explicit removal as it's recreated on mount
      }
    }
  }

  // ✅ NEW: Manual paste button function
  const handleManualPaste = async () => {
    try {
      console.log('📋 Manual paste button clicked')

      if (!navigator.clipboard || !navigator.clipboard.readText) {
        alert('Clipboard API not supported in this browser')
        return
      }

      const text = await navigator.clipboard.readText()
      if (text && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        console.log(`✅ Pasting ${text.length} characters from manual button`)
        wsRef.current.send(JSON.stringify({
          type: 'terminal_input',
          data: text
        }))
      } else if (!text) {
        alert('Clipboard is empty')
      } else {
        alert('Terminal not connected')
      }
    } catch (err) {
      console.error('❌ Manual paste failed:', err)
      alert(`Paste permission denied. Please:\n1. Copy your text\n2. Click inside the terminal\n3. Press Ctrl+V (Windows/Linux) or Cmd+V (Mac)`)
    }
  }

  const connectWebSocket = (term: any) => {
    // ✅ Guard: Close existing WebSocket before creating new one
    if (wsRef.current) {
      console.log('⚠️ Closing existing WebSocket before creating new connection')
      wsRef.current.close()
      wsRef.current = null
    }

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
          {/* ✅ NEW: Manual Paste Button */}
          <button
            onClick={handleManualPaste}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded transition-colors"
            title="Paste from clipboard"
          >
            <Clipboard className="w-3 h-3" />
            <span>Paste</span>
          </button>
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
          Ctrl+C: interrupt • Ctrl+V: paste • Right-click: paste • Type to interact
        </div>
      </div>
    </div>
  )
}
