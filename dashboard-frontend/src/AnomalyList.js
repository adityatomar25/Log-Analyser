import React, { useState, useEffect } from 'react';

function AnomalyList({ sourceKey }) {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setAnomalies([]); // Reset anomalies on source change
    setLoading(true);
    const interval = setInterval(() => {
      fetch('http://localhost:8000/api/anomalies', { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
          setAnomalies(data.anomalies || []);
          setLoading(false);
        })
        .catch(() => {
          setAnomalies([]);
          setLoading(false);
        });
    }, 2000);
    return () => clearInterval(interval);
  }, [sourceKey]);

  return (
    <div>
      <h2>Anomalies</h2>
      {loading ? <div>Waiting for anomalies...</div> :
        anomalies.length === 0 ? <div>No anomalies detected</div> :
        <ul>
          {anomalies.map((a, idx) => <li key={idx} style={{color: 'red'}}>{a}</li>)}
        </ul>
      }
    </div>
  );
}
export default AnomalyList;