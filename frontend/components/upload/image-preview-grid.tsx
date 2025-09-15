"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { StatusBadge } from "@/components/ui/status-badge"
import { X, Edit3 } from "lucide-react"
import { useState } from "react"

interface UploadedImage {
  id: string
  file: File
  name: string
  size: string
  preview: string
  progress: number
  status: "pending" | "uploading" | "completed" | "error"
  error?: string
}

interface ImagePreviewGridProps {
  images: UploadedImage[]
  onUpdateName: (id: string, name: string) => void
  onRemove: (id: string) => void
  disabled?: boolean
}

export function ImagePreviewGrid({ images, onUpdateName, onRemove, disabled }: ImagePreviewGridProps) {
  const [editingId, setEditingId] = useState<string | null>(null)

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {images.map((image) => (
        <Card key={image.id} className="overflow-hidden">
          <CardContent className="p-0">
            {/* Image Preview */}
            <div className="aspect-square bg-muted relative overflow-hidden">
              <img src={image.preview || "/placeholder.svg"} alt={image.name} className="w-full h-full object-cover" />
              <Button
                variant="destructive"
                size="sm"
                className="absolute top-2 right-2 h-6 w-6 p-0"
                onClick={() => onRemove(image.id)}
                disabled={disabled}
              >
                <X className="w-3 h-3" />
              </Button>
              <div className="absolute bottom-2 left-2">
                <StatusBadge status={image.status} size="sm" />
              </div>
            </div>

            {/* Image Info */}
            <div className="p-4 space-y-3">
              {/* Editable Name */}
              <div className="space-y-1">
                {editingId === image.id ? (
                  <Input
                    value={image.name}
                    onChange={(e) => onUpdateName(image.id, e.target.value)}
                    onBlur={() => setEditingId(null)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        setEditingId(null)
                      }
                    }}
                    className="text-sm"
                    autoFocus
                    disabled={disabled}
                  />
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate flex-1" title={image.name}>
                      {image.name}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={() => setEditingId(image.id)}
                      disabled={disabled}
                    >
                      <Edit3 className="w-3 h-3" />
                    </Button>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">{image.size}</p>
              </div>

              {/* Upload Progress */}
              {image.status === "uploading" && (
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span>Uploading...</span>
                    <span>{image.progress}%</span>
                  </div>
                  <Progress value={image.progress} className="h-1" />
                </div>
              )}

              {/* Error Message */}
              {image.status === "error" && image.error && <p className="text-xs text-destructive">{image.error}</p>}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
