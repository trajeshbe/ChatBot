import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import { ThemeProvider } from '@/theme/ThemeProvider'
import { AuthProvider } from '@/contexts/AuthContext'
import { Toaster } from 'react-hot-toast'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider defaultMode="light" storageKey="chatbot-theme">
      <AuthProvider>
        <Component {...pageProps} />
        <Toaster
          position="top-right"
          toastOptions={{
            // Default options
            duration: 5000,
            style: {
              background: '#363636',
              color: '#fff',
              maxWidth: '500px',
            },
            // Success style
            success: {
              duration: 6000,
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            // Error style
            error: {
              duration: 7000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </AuthProvider>
    </ThemeProvider>
  )
}
