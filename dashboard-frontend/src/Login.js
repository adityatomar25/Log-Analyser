import React, { useState } from 'react';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const form = new FormData();
    form.append('username', username);
    form.append('password', password);
    try {
      const res = await fetch('http://localhost:8000/login', {
        method: 'POST',
        body: form,
        credentials: 'include',
      });
      if (res.ok) {
        onLogin();
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
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(120deg, #e0eafc 0%, #cfdef3 100%)',
    }}>
      <div style={{
        maxWidth: 380,
        width: '100%',
        padding: 36,
        background: '#fff',
        borderRadius: 16,
        boxShadow: '0 4px 24px #b0c4de55',
        textAlign: 'center',
      }}>
        <div style={{marginBottom: 24}}>
          <img src="https://cdn-icons-png.flaticon.com/512/1828/1828884.png" alt="Log Analyser" style={{width: 56, marginBottom: 8}} />
          <h2 style={{margin: 0, color: '#2c3e50', fontWeight: 700}}>Log Analyser</h2>
          <div style={{color: '#888', fontSize: 15, marginTop: 4}}>Sign in to continue</div>
        </div>
        <form onSubmit={handleSubmit}>
          <div style={{marginBottom: 16}}>
            <input type="text" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} required style={{width: '100%', padding: 12, borderRadius: 8, border: '1px solid #b0c4de', fontSize: 16}} />
          </div>
          <div style={{marginBottom: 16}}>
            <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required style={{width: '100%', padding: 12, borderRadius: 8, border: '1px solid #b0c4de', fontSize: 16}} />
          </div>
          {error && <div style={{color: '#e74c3c', marginBottom: 12, fontWeight: 500}}>{error}</div>}
          <button type="submit" disabled={loading} style={{width: '100%', padding: 12, background: 'linear-gradient(90deg, #2980b9 0%, #6dd5fa 100%)', color: '#fff', border: 'none', borderRadius: 8, fontSize: 17, fontWeight: 600, boxShadow: '0 2px 8px #b0c4de33', cursor: 'pointer'}}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;
