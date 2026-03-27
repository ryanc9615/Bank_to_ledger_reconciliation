import { useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import { HealthPage } from "./pages/HealthPage";
import { HomePage } from "./pages/HomePage";

type Page = "home" | "health";

function App() {
  const [currentPage, setCurrentPage] = useState<Page>("home");

  return (
    <AppShell currentPage={currentPage} onNavigate={setCurrentPage}>
      {currentPage === "home" && <HomePage />}
      {currentPage === "health" && <HealthPage />}
    </AppShell>
  );
}

export default App;