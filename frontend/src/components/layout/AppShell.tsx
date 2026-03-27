import type { ReactNode } from "react";
import { NavBar } from "./NavBar";

type AppShellProps = {
  currentPage: "home" | "health";
  onNavigate: (page: "home" | "health") => void;
  children: ReactNode;
};

export function AppShell({
  currentPage,
  onNavigate,
  children,
}: AppShellProps) {
  return (
    <div>
      <NavBar currentPage={currentPage} onNavigate={onNavigate} />
      {children}
    </div>
  );
}