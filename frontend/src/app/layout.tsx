import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Roboto and Roboto Mono are vendored under ./fonts/ and served through
// next/font/local. next/font/google makes every cold build depend on a 200
// response from Google that Turbopack can parse, which is the source of the
// "queries have exactly one entry" failure class (vercel/next.js#99114).
const roboto = localFont({
  src: "./fonts/roboto-var-latin.woff2",
  weight: "300 700",
  style: "normal",
  variable: "--font-roboto",
  display: "swap",
  declarations: [
    {
      prop: "unicode-range",
      value:
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    },
  ],
});

const robotoMono = localFont({
  src: "./fonts/roboto-mono-var-latin.woff2",
  weight: "400 700",
  style: "normal",
  variable: "--font-roboto-mono",
  display: "swap",
  declarations: [
    {
      prop: "unicode-range",
      value:
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    },
  ],
});

export const metadata: Metadata = {
  title: "Hinaing – Public Sentiment Monitor",
  description: "Generate actionable public sentiment insights for Baguio City in real-time.",
  icons: {
    icon: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${roboto.variable} ${robotoMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
