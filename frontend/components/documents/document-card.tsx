"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "@/components/ui/status-badge"
import { FileTypeBadge } from "@/components/ui/file-type-badge"
import { Eye, Trash2, Download } from "lucide-react"
import Link from "next/link"

interface Document {
  id: string
  name: string
  uploadDate: string
  type: "image" | "pdf"
  status: "processing" | "completed" | "failed"
  size: string
  thumbnail: string
}

interface DocumentCardProps {
  document: Document
  viewType: "grid" | "list"
}

export function DocumentCard({ document, viewType }: DocumentCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  if (viewType === "list") {
    return (
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            {/* Thumbnail */}
            <div className="w-16 h-16 bg-muted rounded-lg flex-shrink-0 overflow-hidden">
              <img
                src={document.thumbnail || "/placeholder.svg"}
                alt={document.name}
                className="w-full h-full object-cover"
              />
            </div>

            {/* Document Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <h3 className="font-medium text-foreground truncate">{document.name}</h3>
                  <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
                    <span>{formatDate(document.uploadDate)}</span>
                    <span>•</span>
                    <span>{document.size}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <FileTypeBadge type={document.type} size="sm" />
                  <StatusBadge status={document.status} size="sm" />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1 flex-shrink-0">
              <Button asChild variant="ghost" size="sm">
                <Link href={`/document/${document.id}`}>
                  <Eye className="w-4 h-4" />
                </Link>
              </Button>
              <Button variant="ghost" size="sm">
                <Download className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="group hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
      <CardContent className="p-0">
        {/* Thumbnail */}
        <div className="aspect-square bg-muted rounded-t-lg overflow-hidden relative">
          <img
            src={document.thumbnail || "/placeholder.svg"}
            alt={document.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
          />
          <div className="absolute top-2 right-2 flex gap-1">
            <FileTypeBadge type={document.type} size="sm" />
          </div>
          <div className="absolute bottom-2 left-2">
            <StatusBadge status={document.status} size="sm" />
          </div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-3">
          <div className="space-y-1">
            <h3 className="font-medium text-foreground truncate" title={document.name}>
              {document.name}
            </h3>
            <div className="text-sm text-muted-foreground">
              <div>{formatDate(document.uploadDate)}</div>
              <div>{document.size}</div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1">
            <Button asChild variant="outline" size="sm" className="flex-1 bg-transparent">
              <Link href={`/document/${document.id}`}>
                <Eye className="w-4 h-4 mr-1" />
                View Details
              </Link>
            </Button>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" className="text-destructive hover:text-destructive bg-transparent">
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
