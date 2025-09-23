import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css";
import RequireAuth from "@/components/RequireAuth";


const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: "Sofi Agent",
  description: "",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>
        <RequireAuth>{children}</RequireAuth>
      </body>
    </html>
  );
}
