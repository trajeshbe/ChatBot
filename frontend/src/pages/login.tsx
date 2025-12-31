import React, { useState } from 'react';
import { useRouter } from 'next/router';

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    email: string;
    full_name: string | null;
    role: string;
    is_active: boolean;
    created_at: string;
    last_login: string | null;
  };
}

// Horizontal cloud drift - like watching clouds pass by in the sky
const cloudStyles = `
  @keyframes cloud-pass-1 {
    0% {
      transform: translateX(-120%);
      opacity: 0;
    }
    10% {
      opacity: 0.4;
    }
    90% {
      opacity: 0.4;
    }
    100% {
      transform: translateX(120%);
      opacity: 0;
    }
  }

  @keyframes cloud-pass-2 {
    0% {
      transform: translateX(-120%);
      opacity: 0;
    }
    10% {
      opacity: 0.35;
    }
    90% {
      opacity: 0.35;
    }
    100% {
      transform: translateX(120%);
      opacity: 0;
    }
  }

  @keyframes cloud-pass-3 {
    0% {
      transform: translateX(-120%);
      opacity: 0;
    }
    10% {
      opacity: 0.45;
    }
    90% {
      opacity: 0.45;
    }
    100% {
      transform: translateX(120%);
      opacity: 0;
    }
  }

  @keyframes cloud-pass-4 {
    0% {
      transform: translateX(-120%);
      opacity: 0;
    }
    10% {
      opacity: 0.38;
    }
    90% {
      opacity: 0.38;
    }
    100% {
      transform: translateX(120%);
      opacity: 0;
    }
  }

  @keyframes cloud-pass-5 {
    0% {
      transform: translateX(-120%);
      opacity: 0;
    }
    10% {
      opacity: 0.42;
    }
    90% {
      opacity: 0.42;
    }
    100% {
      transform: translateX(120%);
      opacity: 0;
    }
  }

  .cloud-patch {
    position: absolute;
    filter: blur(70px);
    mix-blend-mode: soft-light;
    border-radius: 50%;
    will-change: transform;
  }

  /* Cloud patches positioned in the center area */
  .cloud-1 {
    width: 600px;
    height: 250px;
    top: 20%;
    left: 0;
    background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.6), rgba(107, 144, 128, 0.3), transparent);
    animation: cloud-pass-1 35s linear infinite;
  }

  .cloud-2 {
    width: 700px;
    height: 280px;
    top: 35%;
    left: 0;
    background: radial-gradient(ellipse at center, rgba(107, 144, 128, 0.5), rgba(255, 255, 255, 0.4), transparent);
    animation: cloud-pass-2 42s linear infinite;
    animation-delay: -10s;
  }

  .cloud-3 {
    width: 550px;
    height: 230px;
    top: 50%;
    left: 0;
    background: radial-gradient(ellipse at center, rgba(20, 184, 166, 0.4), rgba(107, 144, 128, 0.4), transparent);
    animation: cloud-pass-3 38s linear infinite;
    animation-delay: -20s;
  }

  .cloud-4 {
    width: 650px;
    height: 270px;
    top: 15%;
    left: 0;
    background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.5), rgba(20, 184, 166, 0.3), transparent);
    animation: cloud-pass-4 40s linear infinite;
    animation-delay: -30s;
  }

  .cloud-5 {
    width: 580px;
    height: 240px;
    top: 60%;
    left: 0;
    background: radial-gradient(ellipse at center, rgba(107, 144, 128, 0.45), rgba(255, 255, 255, 0.5), transparent);
    animation: cloud-pass-5 36s linear infinite;
    animation-delay: -15s;
  }
`;

export default function Login() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Login form submitted', { username });
    setError('');
    setIsLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const loginUrl = `${API_URL}/api/v1/auth/login`;
      console.log('Sending login request to', loginUrl);

      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      console.log('Login response status:', response.status);

      if (!response.ok) {
        const data = await response.json();
        console.error('Login failed:', data);
        throw new Error(data.detail || 'Login failed');
      }

      const data: LoginResponse = await response.json();
      console.log('Login successful:', data.user);

      // Store auth data first
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      console.log('Stored token and user in localStorage');

      // Small delay to ensure localStorage is written
      await new Promise(resolve => setTimeout(resolve, 100));

      console.log('Redirecting to /');
      // Force a full page navigation instead of client-side routing
      window.location.href = '/';

      // Also try router.push as fallback
      // router.push('/');
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <style>{cloudStyles}</style>
      <div className="min-h-screen bg-gradient-to-br from-primary-500 via-primary-400 to-secondary-500 flex items-center justify-center relative overflow-hidden">
        {/* Horizontal Cloud Patches - Passing by like watching the sky */}
        <div className="cloud-patch cloud-1"></div>
        <div className="cloud-patch cloud-2"></div>
        <div className="cloud-patch cloud-3"></div>
        <div className="cloud-patch cloud-4"></div>
        <div className="cloud-patch cloud-5"></div>

        {/* Centered Login Container */}
        <div className="relative z-10 w-full max-w-md px-6">
          {/* Application Branding */}
          <div className="text-center mb-8">
            <h1 className="text-5xl font-bold text-white mb-2 tracking-tight drop-shadow-lg">
              AIR
            </h1>
            <p className="text-white/90 text-lg font-light tracking-wide drop-shadow">
              Enterprise AI Assistant
            </p>
          </div>

          {/* Login Card */}
          <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-white/20">
            <div className="mb-6 text-center">
              <h2 className="text-2xl font-bold text-slate-900 mb-1">Welcome back</h2>
              <p className="text-slate-500 text-sm">Sign in to continue</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="username" className="block text-xs font-semibold text-slate-700 mb-2 uppercase tracking-wide">
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:bg-white transition-all outline-none"
                  placeholder="admin"
                  disabled={isLoading}
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-xs font-semibold text-slate-700 mb-2 uppercase tracking-wide">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:bg-white transition-all outline-none"
                  placeholder="••••••••"
                  disabled={isLoading}
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-primary-600 to-secondary-600 hover:from-primary-700 hover:to-secondary-700 disabled:from-primary-400 disabled:to-secondary-400 text-white font-semibold py-3.5 px-4 rounded-xl shadow-lg hover:shadow-xl hover:-translate-y-0.5 disabled:translate-y-0 transition-all duration-200 flex items-center justify-center"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            <div className="mt-6 p-3.5 bg-gradient-to-r from-primary-50 to-secondary-50 border border-primary-200/50 rounded-xl">
              <div className="flex items-start gap-2">
                <svg className="w-4 h-4 text-primary-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <p className="text-xs font-semibold text-primary-800 mb-1.5">Default Credentials</p>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-primary-700">
                    <span>User: <code className="font-mono font-semibold">admin</code></span>
                    <span>Pass: <code className="font-mono font-semibold">admin</code></span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center text-white/60 text-xs">
            v1.0.0 • Powered by AI
          </div>
        </div>
      </div>
    </>
  );
}
