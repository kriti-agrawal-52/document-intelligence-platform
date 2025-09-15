"use client"

import type React from "react"

import { useCallback, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, Upload } from "lucide-react"
import { cn } from "@/lib/utils"

interface PdfUploadZoneProps {
  onFileSelected: (file: File) => void
  disabled?: boolean
}

export function PdfUploadZone({ onFileSelected, disabled }: PdfUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      if (!disabled) {
        setIsDragOver(true)
      }
    },
    [disabled],
  )

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)

      if (disabled) return

      const files = Array.from(e.dataTransfer.files).filter((file) => file.type === "application/pdf")

      if (files.length > 0) {
        onFileSelected(files[0]) // Only take the first PDF
      }
    },
    [onFileSelected, disabled],
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        onFileSelected(file)
      }
      // Reset input
      e.target.value = ""
    },
    [onFileSelected],
  )

  return (
    <Card
      className={cn(
        "border-2 border-dashed transition-all duration-200",
        isDragOver && !disabled ? "border-primary bg-primary/5" : "border-border",
        disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:border-primary/50",
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <CardContent className="p-12">
        <div className="text-center space-y-6">
          <div
            className={cn(
              "w-20 h-20 rounded-2xl flex items-center justify-center mx-auto transition-colors",
              isDragOver && !disabled ? "bg-primary/20" : "bg-muted",
            )}
          >
            <FileText className={cn("w-10 h-10", isDragOver && !disabled ? "text-primary" : "text-muted-foreground")} />
          </div>

          <div className="space-y-2">
            <h3 className="text-xl font-semibold">{isDragOver ? "Drop PDF here" : "Upload PDF Document"}</h3>
            <p className="text-muted-foreground">Drag & drop a PDF here or click to browse</p>
            <p className="text-sm text-muted-foreground">PDF files up to 10MB • Maximum 20 pages</p>
          </div>

          <div className="space-y-4">
            <input
              type="file"
              accept="application/pdf"
              onChange={handleFileInput}
              className="hidden"
              id="pdf-upload"
              disabled={disabled}
            />
            <Button asChild size="lg" disabled={disabled}>
              <label htmlFor="pdf-upload" className="cursor-pointer">
                <Upload className="w-5 h-5 mr-2" />
                Choose PDF File
              </label>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
