import React, { useState } from 'react';
import config from './config';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    try {
      const res = await fetch(`${config.API_BASE_URL}/login`, {
        method: 'POST',
        body: params,
        credentials: 'include',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      if (res.ok) {
        const data = await res.json();
        onLogin(data.role); // Pass role to parent
      } else {
        const data = await res.json();
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error');
    }
    setLoading(false);
  };

  return (
    <div 
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}
      className="login-container"
    >
      {/* Animated background elements */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '10%',
        width: '200px',
        height: '200px',
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '50%',
        animation: 'float 6s ease-in-out infinite'
      }}></div>
      <div style={{
        position: 'absolute',
        bottom: '15%',
        right: '15%',
        width: '150px',
        height: '150px',
        background: 'rgba(255,255,255,0.05)',
        borderRadius: '50%',
        animation: 'float 8s ease-in-out infinite reverse'
      }}></div>
      
      <div style={{
        maxWidth: 420,
        width: '100%',
        padding: 48,
        background: 'rgba(255, 255, 255, 0.25)',
        backdropFilter: 'blur(20px)',
        borderRadius: 24,
        border: '1px solid rgba(255, 255, 255, 0.18)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
        textAlign: 'center',
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{marginBottom: 32}}>
          <div style={{
            width: 80,
            height: 80,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            boxShadow: '0 10px 30px rgba(102, 126, 234, 0.4)'
          }}>
            <span style={{fontSize: '36px', filter: 'invert(1)'}}>📊</span>
          </div>
          <h1 style={{
            margin: '0 0 8px 0',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            backgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontWeight: 800,
            fontSize: 32,
            letterSpacing: '-0.02em'
          }}>
            Log Analyser
          </h1>
          <p style={{
            color: 'rgba(255, 255, 255, 0.9)',
            fontSize: 16,
            margin: 0,
            fontWeight: 500
          }}>
            AI-Powered Intelligence Dashboard
          </p>
          <p style={{
            color: 'rgba(255, 255, 255, 0.7)',
            fontSize: 14,
            margin: '8px 0 0 0',
            fontWeight: 400
          }}>
            Sign in to access your analytics
          </p>
        </div>
        <form onSubmit={handleSubmit} style={{textAlign: 'left'}}>
          <div style={{marginBottom: 24, position: 'relative'}}>
            <label style={{
              display: 'block',
              marginBottom: 8,
              color: 'rgba(255, 255, 255, 0.9)',
              fontSize: 14,
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Username
            </label>
            <input 
              type="text" 
              placeholder="Enter your username" 
              value={username} 
              onChange={e => setUsername(e.target.value)} 
              required 
              style={{
                width: '100%',
                padding: '16px 20px',
                borderRadius: 16,
                border: 'none',
                background: 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                fontSize: 16,
                color: 'white',
                outline: 'none',
                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s ease',
                boxSizing: 'border-box'
              }}
              onFocus={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.3)';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
              }}
              onBlur={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.2)';
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.1)';
              }}
            />
            <div style={{
              position: 'absolute',
              top: '50%',
              right: 16,
              transform: 'translateY(-50%)',
              color: 'rgba(255, 255, 255, 0.6)',
              fontSize: 18,
              pointerEvents: 'none'
            }}>
              👤
            </div>
          </div>
          
          <div style={{marginBottom: 24, position: 'relative'}}>
            <label style={{
              display: 'block',
              marginBottom: 8,
              color: 'rgba(255, 255, 255, 0.9)',
              fontSize: 14,
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Password
            </label>
            <input 
              type="password" 
              placeholder="Enter your password" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              required 
              style={{
                width: '100%',
                padding: '16px 20px',
                borderRadius: 16,
                border: 'none',
                background: 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                fontSize: 16,
                color: 'white',
                outline: 'none',
                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s ease',
                boxSizing: 'border-box'
              }}
              onFocus={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.3)';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
              }}
              onBlur={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.2)';
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.1)';
              }}
            />
            <div style={{
              position: 'absolute',
              top: '50%',
              right: 16,
              transform: 'translateY(-50%)',
              color: 'rgba(255, 255, 255, 0.6)',
              fontSize: 18,
              pointerEvents: 'none'
            }}>
              🔒
            </div>
          </div>
          
          {error && (
            <div style={{
              background: 'linear-gradient(135deg, #fd79a8 0%, #e84393 100%)',
              color: 'white',
              padding: 16,
              borderRadius: 12,
              marginBottom: 24,
              fontSize: 14,
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: '0 4px 15px rgba(232, 67, 147, 0.3)'
            }}>
              <span style={{fontSize: 16}}>⚠️</span>
              <span>{error}</span>
            </div>
          )}
          
          <button 
            type="submit" 
            disabled={loading} 
            style={{
              width: '100%',
              padding: '16px 24px',
              background: loading 
                ? 'rgba(255, 255, 255, 0.3)' 
                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: 16,
              fontSize: 16,
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: loading 
                ? 'none' 
                : '0 8px 25px rgba(102, 126, 234, 0.4)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              position: 'relative',
              overflow: 'hidden'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 12px 35px rgba(102, 126, 234, 0.5)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 8px 25px rgba(102, 126, 234, 0.4)';
              }
            }}
          >
            {loading ? (
              <span style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8}}>
                <div style={{
                  width: 20,
                  height: 20,
                  border: '2px solid rgba(255,255,255,0.3)',
                  borderTop: '2px solid white',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                Signing In...
              </span>
            ) : (
              <span style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8}}>
                <span>🚀</span>
                Sign In
              </span>
            )}
          </button>
        </form>
        
        {/* Demo credentials hint */}
        <div style={{
          marginTop: 32,
          padding: 20,
          background: 'rgba(255, 255, 255, 0.1)',
          borderRadius: 16,
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
          <p style={{
            margin: '0 0 8px 0',
            color: 'rgba(255, 255, 255, 0.9)',
            fontSize: 14,
            fontWeight: 600
          }}>
            💡 Demo Access
          </p>
          <p style={{
            margin: 0,
            color: 'rgba(255, 255, 255, 0.7)',
            fontSize: 12,
            lineHeight: 1.5
          }}>
            Use <strong>admin/admin</strong> or <strong>user/password</strong>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
