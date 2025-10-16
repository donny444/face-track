import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface AuthState {
  isAuthenticated: boolean;
  instructor: {
    first_name: string;
    last_name: string;
    token: string;
  } | null;
}

const initialState: AuthState = {
  isAuthenticated: false,
  instructor: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    login: (state, action: PayloadAction<{ 
      first_name: string; 
      last_name: string;
      token: string
    }>) => {
      state.isAuthenticated = true;
      state.instructor = action.payload;

      sessionStorage.setItem('first_name', action.payload.first_name);
      sessionStorage.setItem('last_name', action.payload.last_name);
      sessionStorage.setItem('token', action.payload.token);
    },
    logout: (state) => {
      state.isAuthenticated = false;
      state.instructor = null;

      sessionStorage.removeItem('first_name');
      sessionStorage.removeItem('last_name');
      sessionStorage.removeItem('token');
    },
  },
});

export const { login, logout } = authSlice.actions;
export default authSlice.reducer;
