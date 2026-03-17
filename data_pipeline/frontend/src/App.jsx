import { useState } from 'react'
import './App.css'
import CaregiverDashboard from './components/CaregiverDashboard'
import FamilyDashboard from './components/FamilyDashboard'
import ElderlyDashboard from './components/ElderlyDashboard'
import AdminDashboard from './components/AdminDashboard'

function App() {
  const [activeTab, setActiveTab] = useState('login')
  const [role, setRole] = useState('')
  const [username, setUsername] = useState('')

  const handleLogin = (e) => {
    e.preventDefault()
    setActiveTab('dashboard')
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI社区养老数字孪生平台</h1>
      </header>
      <main>
        {activeTab === 'login' ? (
          <div className="login-container">
            <h2>用户登录</h2>
            <div className="login-form">
              <div className="form-group">
                <label>用户名</label>
                <input 
                  type="text" 
                  placeholder="请输入用户名"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>密码</label>
                <input type="password" placeholder="请输入密码" />
              </div>
              <div className="form-group">
                <label>角色</label>
                <select 
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="">请选择角色</option>
                  <option value="caregiver">社区护理人员</option>
                  <option value="family">老人家属</option>
                  <option value="elderly">老年人</option>
                  <option value="admin">系统管理员</option>
                </select>
              </div>
              <button 
                className="login-button"
                onClick={handleLogin}
                disabled={!username || !role}
              >
                登录
              </button>
            </div>
          </div>
        ) : (
          <>
            {role === 'caregiver' && <CaregiverDashboard onLogout={() => setActiveTab('login')} />}
            {role === 'family' && <FamilyDashboard />}
            {role === 'elderly' && <ElderlyDashboard />}
            {role === 'admin' && <AdminDashboard />}
          </>
        )}
      </main>
    </div>
  )
}

export default App
