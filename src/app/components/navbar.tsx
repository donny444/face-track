import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../contexts/store";
import { login, logout } from "../contexts/store/auth_slice.ts";
import { toggleTheme } from "../contexts/store/theme_slice.ts";

export default function Navbar() {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated);
  const username = useSelector((state: RootState) => state.auth.user?.name);
  const theme = useSelector((state: RootState) => state.theme.mode);

  return (
    <nav className={`w-full p-4 ${
      theme === "dark" ? "bg-dark text-white" : "bg-light text-black"
    }`}>
      <button onClick={() => dispatch(toggleTheme())}>{theme}</button>
      {isAuthenticated ? (
        <button onClick={() => dispatch(logout())}>Logout</button>
      ) : (
        <button onClick={undefined}>Login</button>
      )}
      {username && <span>{username}</span>}
    </nav>
  )
}