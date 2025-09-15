"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Eye, EyeOff, FileText, Loader2, Check, X, AlertCircle } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  })

  const router = useRouter()
  const { register, isAuthenticated, loading, error, clearError } = useAuth()

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !loading) {
      router.push("/dashboard")
    }
  }, [isAuthenticated, loading, router])

  // Password strength calculation
  const getPasswordStrength = (password: string) => {
    let strength = 0
    const checks = {
      length: password.length >= 8,
      lowercase: /[a-z]/.test(password),
      uppercase: /[A-Z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    }

    strength = Object.values(checks).filter(Boolean).length
    return { strength: (strength / 5) * 100, checks }
  }

  const passwordStrength = getPasswordStrength(formData.password)

  const getStrengthColor = (strength: number) => {
    if (strength < 40) return "bg-destructive"
    if (strength < 80) return "bg-warning"
    return "bg-success"
  }

  const getStrengthText = (strength: number) => {
    if (strength < 40) return "Weak"
    if (strength < 80) return "Medium"
    return "Strong"
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      clearError()
      await register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
      })
      // Redirect will happen via useEffect when isAuthenticated becomes true
    } catch (error) {
      // Error is handled by the auth context and displayed via error state
      console.error("Registration failed:", error)
    }
  }

  // Show loading spinner while checking auth status
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left side - Hero Section */}
      <div className="hidden lg:flex lg:flex-1 bg-gradient-to-br from-primary/5 to-accent/5 p-12 items-center justify-center">
        <div className="max-w-md text-center space-y-6">
          <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center mx-auto">
            <FileText className="w-8 h-8 text-primary-foreground" />
          </div>
          <div className="space-y-4">
            <h1 className="text-3xl font-bold text-foreground text-balance">Join Document Intelligence Platform</h1>
            <p className="text-lg text-muted-foreground text-pretty">
              Create your account and start transforming documents with AI-powered intelligence today.
            </p>
          </div>
          <div className="w-full h-48 bg-muted rounded-lg flex items-center justify-center">
            <img
              src="/ai-document-analysis-dashboard.jpg"
              alt="AI document analysis dashboard"
              className="w-full h-full object-cover rounded-lg"
            />
          </div>
        </div>
      </div>

      {/* Right side - Registration Form */}
      <div className="flex-1 lg:flex-none lg:w-96 xl:w-[480px] flex items-center justify-center p-6">
        <Card className="w-full max-w-sm">
          <CardHeader className="space-y-1">
            <div className="flex items-center gap-2 mb-4 lg:hidden">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <FileText className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-semibold text-foreground">Document Intelligence</span>
            </div>
            <CardTitle className="text-2xl font-bold">Create Account</CardTitle>
            <CardDescription>Enter your information to get started</CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="Choose a username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
                {formData.username && (
                  <div className="flex items-center gap-2 text-xs">
                    {formData.username.length >= 3 ? (
                      <Check className="w-3 h-3 text-success" />
                    ) : (
                      <X className="w-3 h-3 text-destructive" />
                    )}
                    <span className={formData.username.length >= 3 ? "text-success" : "text-destructive"}>
                      At least 3 characters
                    </span>
                  </div>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
                {formData.email && (
                  <div className="flex items-center gap-2 text-xs">
                    {/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email) ? (
                      <Check className="w-3 h-3 text-success" />
                    ) : (
                      <X className="w-3 h-3 text-destructive" />
                    )}
                    <span
                      className={
                        /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email) ? "text-success" : "text-destructive"
                      }
                    >
                      Valid email address
                    </span>
                  </div>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create a password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                {formData.password && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Progress value={passwordStrength.strength} className="flex-1 h-2" />
                      <span className="text-xs font-medium">{getStrengthText(passwordStrength.strength)}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-1 text-xs">
                      <div className="flex items-center gap-1">
                        {passwordStrength.checks.length ? (
                          <Check className="w-3 h-3 text-success" />
                        ) : (
                          <X className="w-3 h-3 text-destructive" />
                        )}
                        <span className={passwordStrength.checks.length ? "text-success" : "text-destructive"}>
                          8+ chars
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        {passwordStrength.checks.uppercase ? (
                          <Check className="w-3 h-3 text-success" />
                        ) : (
                          <X className="w-3 h-3 text-destructive" />
                        )}
                        <span className={passwordStrength.checks.uppercase ? "text-success" : "text-destructive"}>
                          Uppercase
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        {passwordStrength.checks.lowercase ? (
                          <Check className="w-3 h-3 text-success" />
                        ) : (
                          <X className="w-3 h-3 text-destructive" />
                        )}
                        <span className={passwordStrength.checks.lowercase ? "text-success" : "text-destructive"}>
                          Lowercase
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        {passwordStrength.checks.number ? (
                          <Check className="w-3 h-3 text-success" />
                        ) : (
                          <X className="w-3 h-3 text-destructive" />
                        )}
                        <span className={passwordStrength.checks.number ? "text-success" : "text-destructive"}>
                          Number
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Account...
                  </>
                ) : (
                  "Create Account"
                )}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link href="/login" className="text-primary hover:underline font-medium">
                  Sign in
                </Link>
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
