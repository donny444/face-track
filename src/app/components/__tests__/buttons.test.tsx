import React from "react";
import { render, screen } from "@testing-library/react";
import { ExpandButton, BackButton } from "../buttons";

jest.mock("next/link", () => {
  return {
    __esModule: true,
    default: ({ href, children }: { href: string; children: React.ReactNode }) => (
      <a href={href}>{children}</a>
    ),
  };
});

jest.mock("next/image", () => {
  return {
    __esModule: true,
    default: ({ src, alt, width, height }: { src: string; alt: string; width: number; height: number }) => (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={src} alt={alt} width={width} height={height} />
    ),
  };
});

describe("ExpandButton", () => {
  it("renders an anchor pointing to the supplied route", () => {
    render(<ExpandButton to="/dashboard" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/dashboard");
  });

  it("includes the expand icon image", () => {
    render(<ExpandButton to="/somewhere" />);
    const icon = screen.getByAltText("expand-icon");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveAttribute("src", "/icons/expand_icon.svg");
  });
});

describe("BackButton", () => {
  it("renders an anchor pointing back to the home page", () => {
    render(<BackButton />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/");
  });

  it("includes the back icon image", () => {
    render(<BackButton />);
    const icon = screen.getByAltText("back-icon");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveAttribute("src", "/icons/back_icon.svg");
  });
});
