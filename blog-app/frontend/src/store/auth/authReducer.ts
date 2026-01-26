import type { Reducer } from '@reduxjs/toolkit';
import {
  LOGIN_SUCCESS,
  LOGOUT,
  UPDATE_USER,
  type AuthState,
  type AuthActionTypes,
} from './authTypes';

const initialState: AuthState = {
  isLoggedIn: false,
  user: null,
  token: null,
};

const authReducer: Reducer<AuthState> = (
  state = initialState,
  action
): AuthState => {
  const typedAction = action as AuthActionTypes;

  switch (typedAction.type) {
    case LOGIN_SUCCESS:
      return {
        ...state,
        isLoggedIn: true,
        user: typedAction.payload.user,
        token: typedAction.payload.token || null,
      };
    case LOGOUT:
      return {
        ...state,
        isLoggedIn: false,
        user: null,
        token: null,
      };
    case UPDATE_USER:
      return {
        ...state,
        user: typedAction.payload,
      };
    default:
      return state;
  }
};

export default authReducer;
