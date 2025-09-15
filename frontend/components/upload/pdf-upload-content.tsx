"use client"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { PdfUploadZone } from "@/components/upload/pdf-upload-zone"
import { PdfPreview } from "@/components/upload/pdf-preview"
import { FileText, Upload, CheckCircle, AlertCircle } from "lucide-react"
import Link from "next/link"

interface UploadedPdf {
  id: string
  file: File
  name: string
  size: string
  pageCount?: number
  progress: number
  status: "pending" | "uploading" | "completed" | "error"
  error?: string
}

export function PdfUploadContent() {
  const [pdf, setPdf] = useState<UploadedPdf | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [documentName, setDocumentName] = useState("")

  const handleFileSelected = useCallback((file: File) => {
    const newPdf: UploadedPdf = {
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name.replace(/\.[^/.]+$/, ""), // Remove extension
      size: formatFileSize(file.size),
      pageCount: Math.floor(Math.random() * 20) + 1, // Mock page count
      progress: 0,
      status: "pending",
    }

    setPdf(newPdf)
    setDocumentName(newPdf.name)
  }, [])

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${Number.parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`
  }

  const removePdf = () => {
    setPdf(null)
    setDocumentName("")
  }

  const simulateUpload = async () => {
    if (!pdf) return

    setIsUploading(true)

    // Simulate upload progress
    for (let progress = 0; progress <= 100; progress += 5) {
      await new Promise((resolve) => setTimeout(resolve, 150))
      setPdf((prev) => (prev ? { ...prev, progress, status: "uploading" } : null))
    }

    // Simulate random success/failure
    const success = Math.random() > 0.05 // 95% success rate
    if (success) {
      setPdf((prev) => (prev ? { ...prev, progress: 100, status: "completed" } : null))
    } else {
      setPdf((prev) =>
        prev
          ? {
              ...prev,
              progress: 0,
              status: "error",
              error: "Upload failed. Please check your file and try again.",
            }
          : null,
      )
    }

    setIsUploading(false)
  }

  const handleUpload = async () => {
    if (!pdf) return
    await simulateUpload()
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-foreground">Upload PDF Document</h1>
        <p className="text-muted-foreground">
          Upload a PDF document for AI-powered text extraction and intelligent analysis. Maximum file size: 10MB, up to
          20 pages.
        </p>
      </div>

      {/* Upload Zone */}
      <PdfUploadZone onFileSelected={handleFileSelected} disabled={isUploading} />

      {/* Validation Messages */}
      {pdf?.status === "error" && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{pdf.error}</AlertDescription>
        </Alert>
      )}

      {/* Upload Form */}
      {pdf && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Selected PDF Document
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Document Name */}
            <div className="space-y-2">
              <Label htmlFor="document-name">Document Name</Label>
              <Input
                id="document-name"
                placeholder="Enter document name"
                value={documentName}
                onChange={(e) => setDocumentName(e.target.value)}
                disabled={isUploading}
              />
              <p className="text-sm text-muted-foreground">
                This name will be used to identify your document in the system.
              </p>
            </div>

            {/* PDF Preview */}
            <PdfPreview pdf={pdf} onRemove={removePdf} disabled={isUploading} />

            {/* Upload Progress */}
            {pdf.status === "uploading" && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Uploading and processing...</span>
                  <span>{pdf.progress}%</span>
                </div>
                <Progress value={pdf.progress} className="h-2" />
              </div>
            )}

            {/* Upload Button */}
            <div className="flex items-center justify-between pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                {pdf.size} • {pdf.pageCount} page{pdf.pageCount !== 1 ? "s" : ""}
              </div>
              <div className="flex items-center gap-4">
                <Button variant="outline" onClick={removePdf} disabled={isUploading}>
                  Remove File
                </Button>
                <Button onClick={handleUpload} disabled={!pdf || isUploading || pdf.status === "completed"}>
                  {isUploading ? (
                    <>
                      <Upload className="w-4 h-4 mr-2 animate-pulse" />
                      Processing...
                    </>
                  ) : pdf.status === "completed" ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Completed
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload PDF
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Success State */}
      {pdf?.status === "completed" && (
        <Card className="border-success/20 bg-success/5">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-success/20 rounded-full flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-success" />
              </div>
              <div>
                <h3 className="font-semibold text-success">Upload Successful!</h3>
                <p className="text-sm text-muted-foreground">
                  Your PDF has been uploaded and is being processed for text extraction and analysis.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Button asChild>
                <Link href={`/document/${pdf.id}`}>View Document</Link>
              </Button>
              <Button variant="outline" onClick={() => setPdf(null)}>
                Upload Another PDF
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
