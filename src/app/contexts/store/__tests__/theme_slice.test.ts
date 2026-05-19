import themeReducer, { setTheme, toggleTheme } from "../theme_slice";
import { ThemeEnum } from "@/interfaces/enums";

describe("theme_slice reducer", () => {
  it("defaults to DARK", () => {
    const state = themeReducer(undefined, { type: "@@INIT" });
    expect(state).toEqual({ mode: ThemeEnum.DARK });
  });

  it("setTheme(LIGHT) switches to LIGHT", () => {
    const state = themeReducer(undefined, setTheme(ThemeEnum.LIGHT));
    expect(state.mode).toBe(ThemeEnum.LIGHT);
  });

  it("setTheme(DARK) keeps DARK", () => {
    const state = themeReducer({ mode: ThemeEnum.LIGHT }, setTheme(ThemeEnum.DARK));
    expect(state.mode).toBe(ThemeEnum.DARK);
  });

  it("toggleTheme flips DARK -> LIGHT -> DARK", () => {
    const afterFirstToggle = themeReducer(undefined, toggleTheme());
    expect(afterFirstToggle.mode).toBe(ThemeEnum.LIGHT);
    const afterSecondToggle = themeReducer(afterFirstToggle, toggleTheme());
    expect(afterSecondToggle.mode).toBe(ThemeEnum.DARK);
  });
});
