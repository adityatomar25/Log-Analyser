import './App.css';
import LogList from './LogList';
import AnomalyList from './AnomalyList';
import LogChart from './LogChart';
import SourceSelector from './SourceSelector';
import Login from './Login';
import SearchBar from './SearchBar';
import SystemLogControl from './SystemLogControl';
import BedrockInsights from './BedrockInsights';
import AIAnalytics from './AIAnalytics';
import React, { useState, useEffect } from 'react';

function App() {
  const [sourceKey, setSourceKey] = useState('local');
  const [authenticated, setAuthenticated] = useState(false);
  const [role, setRole] = useState(null);
  const [search, setSearch] = useState(null);
  const [alertsPaused, setAlertsPaused] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('darkMode') === 'true';
  });
  const [apiWarning, setApiWarning] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastApiCall, setLastApiCall] = useState(0);

  useEffect(() => {
    document.body.className = darkMode ? 'dark' : 'light';
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  // Debounced API call helper
  const makeAPICall = (url, options = {}) => {
    const now = Date.now();
    if (now - lastApiCall < 1000) return Promise.resolve(null); // Throttle API calls
    setLastApiCall(now);
    
    return fetch(url, { credentials: 'include', ...options })
      .catch(err => {
        setError('Network connection error');
        setTimeout(() => setError(null), 5000);
        throw err;
      });
  };

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      setLoading(true);
      try {
        const res = await fetch('http://localhost:8000/api/auth/status', { 
          credentials: 'include' 
        });
        
        if (res.ok) {
          const data = await res.json();
          if (data.authenticated) {
            setAuthenticated(true);
            setRole(data.role);
            setError(null);
          } else {
            setAuthenticated(false);
            setRole(null);
          }
        } else {
          setAuthenticated(false);
          setRole(null);
        }
      } catch (err) {
        setAuthenticated(false);
        setRole(null);
        setError('Unable to connect to server');
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  // Fetch alerts paused state with error handling
  useEffect(() => {
    if (authenticated) {
      makeAPICall('http://localhost:8000/alerts/paused')
        .then(res => res ? res.json() : null)
        .then(data => data && setAlertsPaused(data.paused))
        .catch(() => setAlertsPaused(false));
    }
  }, [authenticated]);

  // Handler to pause/resume alerts
  const toggleAlerts = () => {
    fetch('http://localhost:8000/alerts/pause', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paused: !alertsPaused })
    })
      .then(res => res.json())
      .then(data => setAlertsPaused(data.paused));
  };

  // Handler for logout
  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setAuthenticated(false);
      setRole(null);
      setError(null);
    } catch (err) {
      // Even if logout fails on backend, clear frontend state
      setAuthenticated(false);
      setRole(null);
    }
  };

  useEffect(() => {
    const interval = setInterval(() => {
      fetch('http://localhost:8000/api/source_warning', { credentials: 'include' })
        .then(res => res.json())
        .then(data => setApiWarning(data.warning || ""))
        .catch(() => setApiWarning(""));
    }, 2000);
    return () => clearInterval(interval);
  }, [sourceKey]);

  // Loading screen component
  const LoadingScreen = () => (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      flexDirection: 'column',
      gap: '24px'
    }}>
      <div style={{
        width: 80,
        height: 80,
        border: '4px solid rgba(255,255,255,0.3)',
        borderTop: '4px solid white',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }}></div>
      <div style={{
        color: 'white',
        fontSize: 18,
        fontWeight: 600,
        textAlign: 'center'
      }}>
        <div>Connecting to Log Analyser...</div>
        <div style={{fontSize: 14, opacity: 0.8, marginTop: 8}}>
          Please wait while we establish connection
        </div>
      </div>
    </div>
  );

  // Error screen component
  const ErrorScreen = () => (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #fd79a8 0%, #e84393 100%)',
      flexDirection: 'column',
      gap: '24px',
      padding: '20px'
    }}>
      <div style={{fontSize: 64}}>⚠️</div>
      <div style={{
        color: 'white',
        fontSize: 24,
        fontWeight: 700,
        textAlign: 'center'
      }}>
        Connection Error
      </div>
      <div style={{
        color: 'white',
        fontSize: 16,
        textAlign: 'center',
        maxWidth: 400,
        opacity: 0.9
      }}>
        {error || 'Unable to connect to the server. Please check if the backend is running.'}
      </div>
      <button
        onClick={() => window.location.reload()}
        style={{
          padding: '12px 24px',
          background: 'rgba(255,255,255,0.2)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.3)',
          borderRadius: '12px',
          color: 'white',
          fontSize: 16,
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
        onMouseEnter={(e) => {
          e.target.style.background = 'rgba(255,255,255,0.3)';
          e.target.style.transform = 'translateY(-2px)';
        }}
        onMouseLeave={(e) => {
          e.target.style.background = 'rgba(255,255,255,0.2)';
          e.target.style.transform = 'translateY(0)';
        }}
      >
        🔄 Retry Connection
      </button>
    </div>
  );

  if (loading) {
    return <LoadingScreen />;
  }

  if (error && !authenticated) {
    return <ErrorScreen />;
  }

  if (!authenticated) {
    return <Login onLogin={(userRole) => { 
      setAuthenticated(true); 
      setRole(userRole); 
      setError(null);
    }} />;
  }

    return (
      <div 
        style={{
          minHeight: '100vh',
          padding: 0,
          transition: 'all 0.3s ease',
        }}
        data-theme={darkMode ? 'dark' : 'light'}
      >
        {/* Enhanced notification system */}
        {(apiWarning || error) && (
          <div style={{
            background: error 
              ? 'linear-gradient(135deg, #fd79a8 0%, #e84393 100%)'
              : 'linear-gradient(135deg, #fdcb6e 0%, #e17055 100%)',
            color: 'white',
            padding: '16px 32px',
            textAlign: 'center',
            fontWeight: 600,
            fontSize: 14,
            boxShadow: error 
              ? '0 4px 12px rgba(232, 67, 147, 0.3)'
              : '0 4px 12px rgba(253, 203, 110, 0.3)',
            backdropFilter: 'blur(20px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            position: 'relative'
          }}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <span style={{fontSize: '20px'}}>{error ? '⚠️' : '⚡'}</span>
              <span>{error || apiWarning}</span>
            </div>
            <button
              onClick={() => {
                setError(null);
                setApiWarning('');
              }}
              style={{
                background: 'rgba(255,255,255,0.2)',
                border: 'none',
                color: 'white',
                borderRadius: '8px',
                padding: '4px 8px',
                cursor: 'pointer',
                fontSize: '12px',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'rgba(255,255,255,0.3)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'rgba(255,255,255,0.2)';
              }}
            >
              ✕
            </button>
          </div>
        )}
        <header style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '28px 40px 20px 40px',
          background: 'rgba(255, 255, 255, 0.25)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.18)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          borderRadius: '0 0 28px 28px',
          marginBottom: 40,
          transition: 'all 0.3s ease',
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: '20px'}}>
            <div style={{
              width: 48,
              height: 48,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 25px rgba(102, 126, 234, 0.3)'
            }}>
              <span style={{fontSize: '24px', filter: 'invert(1)'}}>📊</span>
            </div>
            <div>
              <h1 style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontWeight: 800,
                fontSize: 32,
                margin: 0,
                letterSpacing: '-0.02em'
              }}>
                Log Analyser
              </h1>
              <p style={{
                margin: 0,
                color: 'rgba(255, 255, 255, 0.8)',
                fontSize: 14,
                fontWeight: 500
              }}>
                AI-Powered Intelligence Dashboard
              </p>
            </div>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: '16px'}}>
            <button 
              onClick={() => setDarkMode(dm => !dm)} 
              className="btn-modern btn-theme-toggle"
              style={{
                padding: '12px 20px',
                background: 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '16px',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600,
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
            >
              <span style={{fontSize: '16px'}}>{darkMode ? '🌙' : '☀️'}</span>
              <span>{darkMode ? 'Dark' : 'Light'}</span>
            </button>
            {role && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '8px 16px',
                background: 'rgba(255, 255, 255, 0.15)',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
              }}>
                <div style={{
                  width: 32,
                  height: 32,
                  background: role === 'admin' 
                    ? 'linear-gradient(135deg, #fd79a8 0%, #e84393 100%)' 
                    : 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '14px'
                }}>
                  {role === 'admin' ? '👑' : '👤'}
                </div>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start'
                }}>
                  <span style={{
                    fontSize: '12px',
                    color: 'rgba(255, 255, 255, 0.8)',
                    fontWeight: 500,
                    textTransform: 'capitalize'
                  }}>
                    {role}
                  </span>
                  <span style={{
                    fontSize: '10px',
                    color: 'rgba(255, 255, 255, 0.6)',
                  }}>
                    Logged in
                  </span>
                </div>
              </div>
            )}
            {role === 'admin' && (
              <button 
                onClick={toggleAlerts} 
                className={`btn-modern ${alertsPaused ? 'btn-danger' : 'btn-success'}`}
                style={{
                  padding: '12px 20px',
                  background: alertsPaused 
                    ? 'linear-gradient(135deg, #fd79a8 0%, #e84393 100%)' 
                    : 'linear-gradient(135deg, #00b894 0%, #00a085 100%)',
                  border: 'none',
                  borderRadius: '16px',
                  cursor: 'pointer',
                  fontSize: 14,
                  fontWeight: 600,
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  boxShadow: alertsPaused 
                    ? '0 4px 15px rgba(232, 67, 147, 0.4)'
                    : '0 4px 15px rgba(0, 184, 148, 0.4)',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                <span style={{fontSize: '16px'}}>{alertsPaused ? '▶️' : '⏸️'}</span>
                <span>{alertsPaused ? 'Resume Alerts' : 'Pause Alerts'}</span>
              </button>
            )}
            <button 
              onClick={handleLogout}
              className="btn-modern btn-logout"
              style={{
                padding: '12px 20px',
                background: 'rgba(255, 255, 255, 0.15)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '16px',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600,
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'linear-gradient(135deg, #fd79a8 0%, #e84393 100%)';
                e.target.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.15)';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              <span style={{fontSize: '16px'}}>🚪</span>
              <span>Logout</span>
            </button>
          </div>
        </header>
        <div style={{maxWidth: 1200, margin: '0 auto', padding: '0 24px'}}>
          <SourceSelector onSourceChange={setSourceKey} />
          <SystemLogControl />
          <BedrockInsights />
          <AIAnalytics sourceKey={sourceKey} />
          <SearchBar onSearch={setSearch} />
          <div style={{display: 'flex', gap: 24, flexWrap: 'wrap'}}>
            <div style={{flex: 2, minWidth: 340}}>
              <LogChart sourceKey={sourceKey} />
            </div>
            <div style={{flex: 1, minWidth: 280}}>
              <AnomalyList sourceKey={sourceKey} />
            </div>
          </div>
          <div>
            <LogList sourceKey={sourceKey} search={search} role={role} />
          </div>
        </div>
      </div>
    );
}

export default App;
