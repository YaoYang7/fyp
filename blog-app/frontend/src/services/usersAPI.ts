import axios from 'axios';

// TODO: Put this into an ENV variable later
const API_BASE_URL = 'http://localhost:8000/user_api'; // Development base URL

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
  tenant_id?: number;
  created_at?: string;
  updated_at?: string;
}

export interface RegisterUser {
  username: string;
  email: string;
  password: string;
  tenant_name: string;
  mode: 'create' | 'join';
}

export const userApi = {

  // Register new user
  register: async (data: RegisterUser): Promise<User> => {
    const response = await api.post('/register', data);
    return response.data;
  },

 
};

export default api;