"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ZoomIn, ZoomOut, ChevronLeft, ChevronRight } from "lucide-react"

interface Document {
  id: string
  name: string
  type: "image" | "pdf"
  thumbnail: string
  pageCount?: number
}

interface DocumentPreviewProps {
  document: Document
}

export function DocumentPreview({ document }: DocumentPreviewProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [zoom, setZoom] = useState(100)

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 200))
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50))
  const handlePrevPage = () => setCurrentPage((prev) => Math.max(prev - 1, 1))
  const handleNextPage = () => setCurrentPage((prev) => Math.min(prev + 1, document.pageCount || 1))

  return (
    <div className="space-y-4">
      {/* Preview Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleZoomOut} disabled={zoom <= 50}>
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-sm font-medium min-w-[60px] text-center">{zoom}%</span>
          <Button variant="outline" size="sm" onClick={handleZoomIn} disabled={zoom >= 200}>
            <ZoomIn className="w-4 h-4" />
          </Button>
        </div>

        {document.type === "pdf" && document.pageCount && document.pageCount > 1 && (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handlePrevPage} disabled={currentPage <= 1}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm font-medium min-w-[80px] text-center">
              {currentPage} of {document.pageCount}
            </span>
            <Button variant="outline" size="sm" onClick={handleNextPage} disabled={currentPage >= document.pageCount}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Preview Area */}
      <div className="border rounded-lg overflow-hidden bg-muted/30">
        <div className="aspect-[3/4] flex items-center justify-center p-4">
          <div
            className="max-w-full max-h-full transition-transform duration-200"
            style={{ transform: `scale(${zoom / 100})` }}
          >
            <img
              src={document.thumbnail || "/placeholder.svg"}
              alt={`${document.name} - Page ${currentPage}`}
              className="max-w-full max-h-full object-contain rounded shadow-lg"
            />
          </div>
        </div>
      </div>

      {/* Preview Info */}
      <div className="text-center text-sm text-muted-foreground">
        {document.type === "image" ? "Image Preview" : `PDF Preview - Page ${currentPage}`}
      </div>
    </div>
  )
}
