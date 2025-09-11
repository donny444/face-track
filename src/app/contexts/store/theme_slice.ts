import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ThemeEnum } from '@/interfaces/enums.ts';

interface ThemeState {
  mode: ThemeEnum;
}

const initialState: ThemeState = {
  mode: ThemeEnum.DARK,
};

const themeSlice = createSlice({
  name: 'theme',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<ThemeEnum>) => {
      state.mode = action.payload;
    },
    toggleTheme: (state) => {
      state.mode = state.mode === ThemeEnum.DARK ? ThemeEnum.LIGHT : ThemeEnum.DARK;
    },
  },
});

export const { setTheme, toggleTheme } = themeSlice.actions;
export default themeSlice.reducer;
