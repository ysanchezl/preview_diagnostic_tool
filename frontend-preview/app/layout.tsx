import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Preview Diagnostico",
  description: "Preview visual de propuestas de automatizacion",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
