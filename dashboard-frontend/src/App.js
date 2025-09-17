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
  const [search, setSearch] = useState(null);

  // Check authentication on mount
  useEffect(() => {
    fetch('http://localhost:8000/api/logs', { credentials: 'include' })
      .then(res => {
        if (res.status === 200) setAuthenticated(true);
        else setAuthenticated(false);
      })
      .catch(() => setAuthenticated(false));
  }, []);

  if (!authenticated) {
    return <Login onLogin={() => setAuthenticated(true)} />;
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(120deg, #e0eafc 0%, #cfdef3 100%)',
      padding: 0,
    }}>
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '24px 40px 16px 40px',
        background: '#fff',
        boxShadow: '0 2px 12px #b0c4de33',
        borderBottomLeftRadius: 24,
        borderBottomRightRadius: 24,
        marginBottom: 32,
      }}>
        <div style={{display: 'flex', alignItems: 'center'}}>
          <img src="https://cdn-icons-png.flaticon.com/512/1828/1828884.png" alt="Log Analyser" style={{width: 40, marginRight: 14}} />
          <h1 style={{color: '#2c3e50', fontWeight: 700, fontSize: 28, margin: 0}}>Log Analyser Dashboard</h1>
        </div>
        <div>
          {/* Placeholder for user menu or logout */}
        </div>
      </header>
      <div style={{maxWidth: 1200, margin: '0 auto', padding: '0 24px'}}>
        <SourceSelector onSourceChange={setSourceKey} />
        <SearchBar onSearch={setSearch} />
        <div style={{display: 'flex', gap: 24, flexWrap: 'wrap'}}>
          <div style={{flex: 2, minWidth: 340, background: '#fff', borderRadius: 16, boxShadow: '0 2px 12px #b0c4de33', padding: 24, marginBottom: 24}}>
            <LogChart sourceKey={sourceKey} />
          </div>
          <div style={{flex: 1, minWidth: 280, background: '#fff', borderRadius: 16, boxShadow: '0 2px 12px #b0c4de33', padding: 24, marginBottom: 24}}>
            <AnomalyList sourceKey={sourceKey} />
          </div>
        </div>
        <div style={{background: '#fff', borderRadius: 16, boxShadow: '0 2px 12px #b0c4de33', padding: 24, marginBottom: 24}}>
          <LogList sourceKey={sourceKey} search={search} />
        </div>
      </div>
    </div>
  );
}

export default App;
