import { useState, useEffect } from 'react'
import './index.css'

function App() {
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [signing, setSigning] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    fetchPolicies()
  }, [])

  const fetchPolicies = async () => {
    try {
      // In development Vite runs on 5173, FastAPI on 3000
      const baseUrl = window.location.port === '5173' ? 'http://127.0.0.1:3000' : ''
      const res = await fetch(`${baseUrl}/api/policies`)
      const data = await res.json()
      setPolicies(data.policies || [])
    } catch (err) {
      console.error(err)
      setMessage({ type: 'error', text: 'Failed to connect to FileGit Studio API.' })
    } finally {
      setLoading(false)
    }
  }

  const handleSign = async () => {
    setSigning(true)
    setMessage(null)
    try {
      const baseUrl = window.location.port === '5173' ? 'http://127.0.0.1:3000' : ''
      const res = await fetch(`${baseUrl}/api/pack`, {
        method: 'POST'
      })
      
      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to sign policies')
      }
      
      setMessage({ 
        type: 'success', 
        text: `Success! Context Bundle Signed: ${data.manifest.bundle_id}` 
      })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setSigning(false)
    }
  }

  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto' }}>
      <header style={{ marginBottom: '40px', textAlign: 'center' }} className="animate-fade-in">
        <h1 style={{ fontSize: '3rem', marginBottom: '8px', background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          FileGit Studio
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.2rem' }}>
          Enterprise Governance & Context Attestation
        </p>
      </header>

      {message && (
        <div 
          className="glass-panel animate-fade-in" 
          style={{ 
            marginBottom: '24px', 
            borderLeft: `4px solid ${message.type === 'error' ? 'var(--accent-danger)' : 'var(--accent-success)'}` 
          }}
        >
          {message.text}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '24px' }}>
        <div className="glass-panel animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <h2>Authorized Policies</h2>
          {loading ? (
            <p>Loading context...</p>
          ) : policies.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)' }}>No policies found in the repository.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '20px' }}>
              {policies.map((policy, idx) => (
                <div key={idx} style={{ padding: '16px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '1.1rem' }}>{policy.title}</h3>
                  <code style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{policy.path}</code>
                  <pre style={{ 
                    marginTop: '12px', 
                    padding: '12px', 
                    background: 'rgba(0,0,0,0.3)', 
                    borderRadius: '6px',
                    fontSize: '0.9rem',
                    overflowX: 'auto',
                    color: 'var(--text-primary)'
                  }}>
                    {policy.content}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-panel animate-fade-in" style={{ animationDelay: '0.2s', height: 'fit-content' }}>
          <h2>CISO Approval</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontSize: '0.9rem' }}>
            Review the policies on the left. Click below to cryptographically sign the context bundle and authorize AI Agents to operate.
          </p>
          <button 
            className="btn" 
            style={{ width: '100%' }}
            onClick={handleSign}
            disabled={signing || loading || policies.length === 0}
          >
            {signing ? 'Signing...' : 'Sign & Authorize Context'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
