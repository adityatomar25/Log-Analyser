import './App.css';
import LogList from './LogList';
import AnomalyList from './AnomalyList';
import LogChart from './LogChart';
import SourceSelector from './SourceSelector';
import Login from './Login';
import SearchBar from './SearchBar';
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

  useEffect(() => {
    document.body.className = darkMode ? 'dark' : 'light';
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  // Check authentication on mount
  useEffect(() => {
    fetch('http://localhost:8000/api/logs', { credentials: 'include' })
      .then(res => {
        if (res.status === 200) setAuthenticated(true);
        else setAuthenticated(false);
      })
      .catch(() => setAuthenticated(false));
  }, []);

  // Fetch alerts paused state
  useEffect(() => {
    fetch('http://localhost:8000/alerts/paused', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setAlertsPaused(data.paused))
      .catch(() => setAlertsPaused(false));
  }, []);

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

  if (!authenticated) {
    return <Login onLogin={r => { setAuthenticated(true); setRole(r); }} />;
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: darkMode ? 'linear-gradient(120deg, #232526 0%, #414345 100%)' : 'linear-gradient(120deg, #e0eafc 0%, #cfdef3 100%)',
      padding: 0,
      transition: 'background 0.3s',
    }}>
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '24px 40px 16px 40px',
        background: darkMode ? '#23272f' : '#fff',
        boxShadow: '0 2px 12px #b0c4de33',
        borderBottomLeftRadius: 24,
        borderBottomRightRadius: 24,
        marginBottom: 32,
        transition: 'background 0.3s',
      }}>
        <div style={{display: 'flex', alignItems: 'center'}}>
          <img src="https://cdn-icons-png.flaticon.com/512/1828/1828884.png" alt="Log Analyser" style={{width: 40, marginRight: 14, filter: darkMode ? 'invert(1)' : 'none'}} />
          <h1 style={{color: darkMode ? '#f0f4f8' : '#2c3e50', fontWeight: 700, fontSize: 28, margin: 0}}>Log Analyser Dashboard</h1>
        </div>
        <div>
          <button onClick={() => setDarkMode(dm => !dm)} className="button-primary" style={{marginRight: 16}}>
            {darkMode ? '🌙 Dark' : '☀️ Light'}
          </button>
          <span style={{fontWeight: 500, color: darkMode ? '#6dd5fa' : '#2980b9', marginRight: 16}}>{role ? `Role: ${role}` : ''}</span>
          {role === 'admin' && (
            <button onClick={toggleAlerts} className="button-primary" style={{background: alertsPaused ? '#e74c3c' : undefined}}>
              {alertsPaused ? 'Resume Alerts' : 'Pause Alerts'}
            </button>
          )}
        </div>
      </header>
      <div style={{maxWidth: 1200, margin: '0 auto', padding: '0 24px'}}>
        <SourceSelector onSourceChange={setSourceKey} />
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
