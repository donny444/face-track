'use client';

import Image from "next/image"

import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../contexts/store";
import { login, logout } from "../contexts/store/auth_slice.ts";
import { toggleTheme } from "../contexts/store/theme_slice.ts";

import { ThemeEnum } from "@/interfaces/enums.ts"

export default function Navbar() {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated);
  const username = useSelector((state: RootState) => state.auth.user?.name);
  const theme = useSelector((state: RootState) => state.theme.mode);

  return (
    <nav className={`w-full p-4 mb-4 ${
      theme === ThemeEnum.DARK ? "bg-dark text-white" : "bg-light text-black"
    }`}>
      <Image
        src={`${theme === ThemeEnum.DARK ? "/icons/dark_icon.svg" : "/icons/light_icon.svg"}`}
        alt="theme-icon"
        width={50}
        height={50}
        onClick={() => dispatch(toggleTheme())}
      />
      {isAuthenticated ? (
        <button
          className={`btn 
            ${theme === ThemeEnum.DARK ? "btn-success" : "btn-primary"}    
          `}
          onClick={() => dispatch(logout())}
        >
          Logout
        </button>
      ) : (
        <button
          className={`btn 
            ${theme === ThemeEnum.DARK ? "btn-success" : "btn-primary"}  
          `}
          onClick={undefined}
        >
          Login
        </button>
      )}
      {username && <span>{username}</span>}
    </nav>
  )
}