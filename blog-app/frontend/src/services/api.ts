import axios from 'axios';

// TODO: Put this into an ENV variable later
const API_BASE_URL = 'http://localhost:8000/api'; // Development base URL

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface User {
  id?: number;
  username: string;
  email: string;
  full_name: string;
  is_active?: boolean;
  is_admin?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface UserCreate extends User {
  password: string;
}

export interface UserUpdate {
  username?: string;
  email?: string;
  full_name?: string;
  is_active?: boolean;
  is_admin?: boolean;
}

export interface PasswordUpdate {
  current_password: string;
  new_password: string;
}

export const userApi = {
  // Get all users
  getUsers: async (search?: string): Promise<User[]> => {
    const params = search ? { search } : {};
    const response = await api.get('/users', { params });
    return response.data;
  },

  // Get single user
  getUser: async (id: number): Promise<User> => {
    const response = await api.get(`/users/${id}`);
    return response.data;
  },

  // Create user
  createUser: async (user: UserCreate): Promise<User> => {
    const response = await api.post('/users', user);
    return response.data;
  },

  // Update user
  updateUser: async (id: number, user: UserUpdate): Promise<User> => {
    const response = await api.put(`/users/${id}`, user);
    return response.data;
  },

  // Update password
  updatePassword: async (id: number, passwords: PasswordUpdate): Promise<void> => {
    await api.put(`/users/${id}/password`, passwords);
  },

  // Delete user
  deleteUser: async (id: number): Promise<void> => {
    await api.delete(`/users/${id}`);
  },
};

export default api;