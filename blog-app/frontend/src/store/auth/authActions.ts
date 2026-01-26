import {
  LOGIN_SUCCESS,
  LOGOUT,
  UPDATE_USER,
  type AuthActionTypes,
  type User,
} from './authTypes';

export const loginSuccess = (user: User, token?: string): AuthActionTypes => ({
  type: LOGIN_SUCCESS,
  payload: { user, token },
});

export const logout = (): AuthActionTypes => ({
  type: LOGOUT,
});

export const updateUser = (user: User): AuthActionTypes => ({
  type: UPDATE_USER,
  payload: user,
});
