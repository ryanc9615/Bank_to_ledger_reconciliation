import type { ReactNode } from "react";

type PageContainerProps = {
  title: string;
  children: ReactNode;
};

export function PageContainer({ title, children }: PageContainerProps) {
  return (
    <main style={{ padding: "24px", maxWidth: "960px", margin: "0 auto" }}>
      <h1>{title}</h1>
      <div>{children}</div>
    </main>
  );
}