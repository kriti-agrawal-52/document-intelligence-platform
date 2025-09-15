import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { FileText, ImageIcon, Search } from "lucide-react"
import Link from "next/link"

interface DocumentsEmptyStateProps {
  hasSearch: boolean
  searchQuery?: string
  filterType?: string
}

export function DocumentsEmptyState({ hasSearch, searchQuery, filterType }: DocumentsEmptyStateProps) {
  if (hasSearch) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No documents found</h3>
          <p className="text-muted-foreground mb-6">
            {searchQuery
              ? `No documents match "${searchQuery}"`
              : `No ${filterType === "image" ? "images" : filterType === "pdf" ? "PDFs" : "documents"} found`}
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button asChild>
              <Link href="/upload/images">
                <ImageIcon className="w-4 h-4 mr-2" />
                Upload Images
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/upload/pdf">
                <FileText className="w-4 h-4 mr-2" />
                Upload PDF
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="text-center py-16">
        <div className="w-20 h-20 bg-muted rounded-full flex items-center justify-center mx-auto mb-6">
          <FileText className="w-10 h-10 text-muted-foreground" />
        </div>
        <h3 className="text-xl font-semibold mb-3">No documents yet</h3>
        <p className="text-muted-foreground mb-8 max-w-md mx-auto">
          Start by uploading your first document to get started with AI-powered document intelligence.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Button asChild size="lg">
            <Link href="/upload/images">
              <ImageIcon className="w-5 h-5 mr-2" />
              Upload Images
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/upload/pdf">
              <FileText className="w-5 h-5 mr-2" />
              Upload PDF
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
