import authReducer, { login, logout } from "../auth_slice";

describe("auth_slice reducer", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("returns the initial state when called with @@INIT", () => {
    const state = authReducer(undefined, { type: "@@INIT" });
    expect(state).toEqual({ isAuthenticated: false, instructor: null });
  });

  it("login flips isAuthenticated, stores the instructor and persists to sessionStorage", () => {
    const payload = { first_name: "Pat", last_name: "Prof", token: "abc.def.ghi" };
    const state = authReducer(undefined, login(payload));

    expect(state.isAuthenticated).toBe(true);
    expect(state.instructor).toEqual(payload);
    expect(sessionStorage.getItem("first_name")).toBe("Pat");
    expect(sessionStorage.getItem("last_name")).toBe("Prof");
    expect(sessionStorage.getItem("token")).toBe("abc.def.ghi");
  });

  it("logout clears auth state and sessionStorage", () => {
    const loggedIn = authReducer(
      undefined,
      login({ first_name: "Pat", last_name: "Prof", token: "tok" })
    );

    const state = authReducer(loggedIn, logout());

    expect(state.isAuthenticated).toBe(false);
    expect(state.instructor).toBeNull();
    expect(sessionStorage.getItem("first_name")).toBeNull();
    expect(sessionStorage.getItem("last_name")).toBeNull();
    expect(sessionStorage.getItem("token")).toBeNull();
  });
});
