"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { StatusBadge } from "@/components/ui/status-badge"
import { FileText, X } from "lucide-react"

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

interface PdfPreviewProps {
  pdf: UploadedPdf
  onRemove: () => void
  disabled?: boolean
}

export function PdfPreview({ pdf, onRemove, disabled }: PdfPreviewProps) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        <div className="flex items-center gap-4 p-4">
          {/* PDF Thumbnail */}
          <div className="w-16 h-20 bg-muted rounded-lg flex items-center justify-center flex-shrink-0 relative">
            <FileText className="w-8 h-8 text-muted-foreground" />
            <div className="absolute -top-1 -right-1">
              <StatusBadge status={pdf.status} size="sm" />
            </div>
          </div>

          {/* PDF Info */}
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <h3 className="font-medium text-foreground truncate" title={pdf.name}>
                  {pdf.name}
                </h3>
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <span>{pdf.size}</span>
                  {pdf.pageCount && (
                    <>
                      <span>•</span>
                      <span>
                        {pdf.pageCount} page{pdf.pageCount !== 1 ? "s" : ""}
                      </span>
                    </>
                  )}
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onRemove}
                disabled={disabled}
                className="text-destructive hover:text-destructive"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            {/* Error Message */}
            {pdf.status === "error" && pdf.error && <p className="text-sm text-destructive">{pdf.error}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
