'use client';

import Image from "next/image"
import Link from "next/link";

import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../contexts/store";
import { login, logout } from "../contexts/store/auth_slice.ts";
import { toggleTheme } from "../contexts/store/theme_slice.ts";

import "bootstrap/dist/css/bootstrap.min.css";
import { Button } from "react-bootstrap";

import { ThemeEnum } from "@/interfaces/enums.ts"

export default function Navbar() {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated);
  const firstName = useSelector((state: RootState) => state.auth.instructor?.first_name);
  const lastName = useSelector((state: RootState) => state.auth.instructor?.last_name);
  const themeMode = useSelector((state: RootState) => state.theme.mode);

  const token = sessionStorage.getItem('token');
  if (token && !isAuthenticated) {
    dispatch(login({
      first_name: sessionStorage.getItem('first_name') || '',
      last_name: sessionStorage.getItem('last_name') || '',
      token: token
    }))
  }

  return (
    <nav className={`w-full p-4 mb-4 d-flex flex-row justify-content-between align-items-center ${
      themeMode === ThemeEnum.DARK ? "bg-dark text-white" : "bg-light text-black"
    }`}>
      <Image
        src={`${themeMode === ThemeEnum.DARK ? "/icons/dark_icon.svg" : "/icons/light_icon.svg"}`}
        alt="theme-icon"
        width={50}
        height={50}
        onClick={() => dispatch(toggleTheme())}
      />
      {isAuthenticated ? (
        <div className="d-flex flew-row align-items-center">
          <p className="mb-0"><span>{firstName}</span> <span>{lastName}</span></p>
          <Button
            className="ms-2"
            variant="danger"
            onClick={() => dispatch(logout())}
          >
            Logout
          </Button>
        </div>
      ) : (
        <div>
          <Link href="/login">
            <Button
              className="me-2"
              variant={`${themeMode === ThemeEnum.DARK ? "success" : "primary"}`}
              onClick={undefined}
            >
              Login
            </Button>
          </Link>
          <Link href="/register">
            <Button
              variant={`${themeMode === ThemeEnum.DARK ? "primary" : "success"}`}
              onClick={undefined}
            >
              Register
            </Button>
          </Link>
        </div>
      )}
    </nav>
  )
}