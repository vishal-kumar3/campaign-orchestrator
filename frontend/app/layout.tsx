import type { Metadata } from 'next'
import Link from 'next/link'
import { ClerkProvider, Show, SignInButton, SignUpButton, UserButton } from '@clerk/nextjs'
import { Geist, Geist_Mono } from 'next/font/google'

import { Providers } from '@/components/providers'
import './globals.css'

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
})

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'Campaign Orchestrator',
  description: 'Manage workspaces, campaigns, and knowledge bases',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <ClerkProvider>
          <Providers>
            <div className="flex min-h-screen flex-col">
              <header className="sticky top-0 z-40 border-b bg-background">
                <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-4 lg:px-6">
                  <Link href="/dashboard" className="text-sm font-semibold tracking-tight">
                    Campaign Orchestrator
                  </Link>
                  <div className="flex items-center gap-3">
                    <Show when="signed-out">
                      <SignInButton />
                      <SignUpButton>
                        <button className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground">
                          Sign up
                        </button>
                      </SignUpButton>
                    </Show>
                    <Show when="signed-in">
                      <UserButton />
                    </Show>
                  </div>
                </div>
              </header>
              {children}
            </div>
          </Providers>
        </ClerkProvider>
      </body>
    </html>
  )
}
