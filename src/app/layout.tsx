import type { Metadata } from "next";
import localFont from "next/font/local";

import "./globals.css";
// import "bootstrap/dist/css/bootstrap.min.css";

import Navbar from "./components/navbar.tsx";

import ReduxProvider from "./contexts/redux_provider.tsx";

const ibmPlexSansThai = localFont({
  variable: "--font-ibm-plex-sans-thai",
  display: "swap",
  src: [
    {
      path: "./fonts/IBMPlexSansThai-Thin.ttf",
      weight: "100",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-ExtraLight.ttf",
      weight: "200",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-Light.ttf",
      weight: "300",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-Regular.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-Medium.ttf",
      weight: "500",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-SemiBold.ttf",
      weight: "600",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-Bold.ttf",
      weight: "700",
      style: "normal",
    },
  ],
});

const ibmPlexSansThaiMono = localFont({
  variable: "--font-ibm-plex-sans-thai-mono",
  display: "swap",
  src: [
    {
      path: "./fonts/IBMPlexSansThai-Thin.ttf",
      weight: "100",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-ExtraLight.ttf",
      weight: "200",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-Light.ttf",
      weight: "300",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-Regular.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-Medium.ttf",
      weight: "500",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-SemiBold.ttf",
      weight: "600",
      style: "normal",
    },
    {
      path: "./fonts/IBMPlexSansThai-Bold.ttf",
      weight: "700",
      style: "normal",
    },
  ],
});

export const metadata: Metadata = {
  title: "FaceTrack",
  description: "Application for monitoring student attendance in a class",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${ibmPlexSansThai.variable} ${ibmPlexSansThaiMono.variable}`}
      >
        <ReduxProvider>
          <Navbar />
          {children}
        </ReduxProvider>
      </body>
    </html>
  );
}
