export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
  updated_at?: string;
}

export interface AuthState {
  isLoggedIn: boolean;
  user: User | null;
  token: string | null;
}

export const LOGIN_SUCCESS = 'auth/LOGIN_SUCCESS';
export const LOGOUT = 'auth/LOGOUT';
export const UPDATE_USER = 'auth/UPDATE_USER';

export type AuthActionTypes =
  | { type: typeof LOGIN_SUCCESS; payload: { user: User; token?: string } }
  | { type: typeof LOGOUT }
  | { type: typeof UPDATE_USER; payload: User };