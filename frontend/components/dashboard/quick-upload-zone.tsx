"use client"

import type React from "react"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"

interface QuickUploadZoneProps {
  type: "images" | "pdf"
  title: string
  description: string
  icon: React.ReactNode
  href: string
  className?: string
}

export function QuickUploadZone({ type, title, description, icon, href, className }: QuickUploadZoneProps) {
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    // In a real app, handle file drop here
    console.log("Files dropped:", e.dataTransfer.files)
  }

  return (
    <Card
      className={cn(
        "border-2 border-dashed border-border hover:border-primary/50 transition-colors cursor-pointer group",
        className,
      )}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <CardContent className="p-8">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto group-hover:bg-primary/20 transition-colors">
            <div className="text-primary">{icon}</div>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">{title}</h3>
            <p className="text-sm text-muted-foreground">Drag & drop {type} here or click to browse</p>
            <p className="text-xs text-muted-foreground">{description}</p>
          </div>
          <Button asChild className="w-full">
            <Link href={href}>
              <Upload className="w-4 h-4 mr-2" />
              Choose {type === "images" ? "Image Files" : "PDF File"}
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
