import { configureStore } from '@reduxjs/toolkit';
import authReducer from './auth_slice.ts';
import themeReducer from './theme_slice.ts';

const store = configureStore({
  reducer: {
    auth: authReducer,
    theme: themeReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export default store;
