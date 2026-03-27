import { useEffect, useState } from "react";

import { apiGet } from "../api/client";
import { PageContainer } from "../components/ui/PageContainer";
import type { HealthResponse } from "../types/health";

export function HealthPage() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHealth() {
      try {
        const result = await apiGet<HealthResponse>("/health");
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchHealth();
  }, []);

  return (
    <PageContainer title="API Health Check">
      {loading && <p>Loading...</p>}
      {error && <p>Error: {error}</p>}
      {data && (
        <div>
          <p>Status: {data.status}</p>
          <p>Service: {data.service}</p>
          <p>Environment: {data.environment}</p>
        </div>
      )}
    </PageContainer>
  );
}