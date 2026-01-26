import { useState, useEffect } from 'react'
import axios from 'axios'

interface User {
  id: number
  username: string
  email: string
  created_at: string
}

function Users() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await axios.get('http://localhost:8000/api/users')
      setUsers(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch users')
      console.error('Error fetching users:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="container">Loading...</div>
  }

  if (error) {
    return <div className="container error">{error}</div>
  }

  return (
    <div className="container">
      <h1>User Management</h1>
      
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center' }}>
                  No users found
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>{user.username}</td>
                  <td>{user.email}</td>
                  <td>{new Date(user.created_at).toLocaleDateString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <button onClick={fetchUsers} className="refresh-btn">
        Refresh Users
      </button>
    </div>
  )
}

export default Users