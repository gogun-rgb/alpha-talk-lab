import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AlphaTalk Lab",
  description: "말로 하는 투자 리서치 실험실"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
