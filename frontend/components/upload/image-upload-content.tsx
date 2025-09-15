"use client"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ImageUploadZone } from "@/components/upload/image-upload-zone"
import { ImagePreviewGrid } from "@/components/upload/image-preview-grid"
import { ImageIcon, Upload, CheckCircle, AlertCircle } from "lucide-react"
import Link from "next/link"

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

export function ImageUploadContent() {
  const [images, setImages] = useState<UploadedImage[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [batchName, setBatchName] = useState("")

  const handleFilesSelected = useCallback((files: File[]) => {
    const validFiles = files.filter((file) => {
      const isValidType = ["image/png", "image/jpeg", "image/jpg"].includes(file.type)
      const isValidSize = file.size <= 10 * 1024 * 1024 // 10MB
      return isValidType && isValidSize
    })

    const newImages: UploadedImage[] = validFiles.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: formatFileSize(file.size),
      preview: URL.createObjectURL(file),
      progress: 0,
      status: "pending",
    }))

    setImages((prev) => [...prev, ...newImages])
  }, [])

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${Number.parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`
  }

  const updateImageName = (id: string, newName: string) => {
    setImages((prev) => prev.map((img) => (img.id === id ? { ...img, name: newName } : img)))
  }

  const removeImage = (id: string) => {
    setImages((prev) => {
      const imageToRemove = prev.find((img) => img.id === id)
      if (imageToRemove) {
        URL.revokeObjectURL(imageToRemove.preview)
      }
      return prev.filter((img) => img.id !== id)
    })
  }

  const simulateUpload = async (image: UploadedImage) => {
    const updateProgress = (progress: number, status: UploadedImage["status"]) => {
      setImages((prev) => prev.map((img) => (img.id === image.id ? { ...img, progress, status } : img)))
    }

    updateProgress(0, "uploading")

    // Simulate upload progress
    for (let progress = 0; progress <= 100; progress += 10) {
      await new Promise((resolve) => setTimeout(resolve, 200))
      updateProgress(progress, "uploading")
    }

    // Simulate random success/failure
    const success = Math.random() > 0.1 // 90% success rate
    if (success) {
      updateProgress(100, "completed")
    } else {
      updateProgress(0, "error")
      setImages((prev) =>
        prev.map((img) => (img.id === image.id ? { ...img, error: "Upload failed. Please try again." } : img)),
      )
    }
  }

  const handleUpload = async () => {
    if (images.length === 0) return

    setIsUploading(true)

    // Upload all images concurrently
    const uploadPromises = images.filter((img) => img.status === "pending").map((image) => simulateUpload(image))

    await Promise.all(uploadPromises)
    setIsUploading(false)
  }

  const completedImages = images.filter((img) => img.status === "completed")
  const hasErrors = images.some((img) => img.status === "error")

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-foreground">Upload Images</h1>
        <p className="text-muted-foreground">
          Upload multiple images for AI-powered text extraction and analysis. Supported formats: PNG, JPG, JPEG.
        </p>
      </div>

      {/* Upload Zone */}
      <ImageUploadZone onFilesSelected={handleFilesSelected} disabled={isUploading} />

      {/* Validation Messages */}
      {hasErrors && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Some images failed to upload. Please check the errors below and try again.
          </AlertDescription>
        </Alert>
      )}

      {/* Upload Form */}
      {images.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="w-5 h-5" />
              Selected Images ({images.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Batch Naming */}
            <div className="space-y-2">
              <Label htmlFor="batch-name">Batch Name (Optional)</Label>
              <Input
                id="batch-name"
                placeholder="e.g., Invoice Batch 2024-01"
                value={batchName}
                onChange={(e) => setBatchName(e.target.value)}
                disabled={isUploading}
              />
              <p className="text-sm text-muted-foreground">
                This name will be used as a prefix for all images in this batch.
              </p>
            </div>

            {/* Image Preview Grid */}
            <ImagePreviewGrid
              images={images}
              onUpdateName={updateImageName}
              onRemove={removeImage}
              disabled={isUploading}
            />

            {/* Upload Button */}
            <div className="flex items-center justify-between pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                {images.length} image{images.length !== 1 ? "s" : ""} ready for upload
              </div>
              <div className="flex items-center gap-4">
                <Button variant="outline" onClick={() => setImages([])} disabled={isUploading}>
                  Clear All
                </Button>
                <Button onClick={handleUpload} disabled={images.length === 0 || isUploading}>
                  {isUploading ? (
                    <>
                      <Upload className="w-4 h-4 mr-2 animate-pulse" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Images
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Success State */}
      {completedImages.length > 0 && !isUploading && (
        <Card className="border-success/20 bg-success/5">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-success/20 rounded-full flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-success" />
              </div>
              <div>
                <h3 className="font-semibold text-success">Upload Successful!</h3>
                <p className="text-sm text-muted-foreground">
                  {completedImages.length} image{completedImages.length !== 1 ? "s" : ""} uploaded and processing.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Button asChild>
                <Link href="/documents">View Documents</Link>
              </Button>
              <Button variant="outline" onClick={() => setImages([])}>
                Upload More Images
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
