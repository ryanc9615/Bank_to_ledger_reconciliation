type NavBarProps = {
  currentPage: "home" | "health";
  onNavigate: (page: "home" | "health") => void;
};

export function NavBar({ currentPage, onNavigate }: NavBarProps) {
  return (
    <nav
      style={{
        display: "flex",
        gap: "12px",
        padding: "16px 24px",
        borderBottom: "1px solid #ddd",
        backgroundColor: "#fff",
      }}
    >
      <button
        onClick={() => onNavigate("home")}
        disabled={currentPage === "home"}
      >
        Home
      </button>

      <button
        onClick={() => onNavigate("health")}
        disabled={currentPage === "health"}
      >
        API Health
      </button>
    </nav>
  );
}