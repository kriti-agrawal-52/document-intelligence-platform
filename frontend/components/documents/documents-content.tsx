"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DocumentCard } from "@/components/documents/document-card"
import { DocumentsEmptyState } from "@/components/documents/documents-empty-state"
import { ImageIcon, FileText, Search, Grid3X3, List } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"

// Mock data for documents
const mockDocuments = [
  {
    id: "1",
    name: "Invoice_2024_001.pdf",
    uploadDate: "2024-01-15T10:30:00Z",
    type: "pdf" as const,
    status: "completed" as const,
    size: "2.4 MB",
    thumbnail: "/pdf-thumbnail.png",
  },
  {
    id: "2",
    name: "Receipt_grocery.jpg",
    uploadDate: "2024-01-14T15:45:00Z",
    type: "image" as const,
    status: "processing" as const,
    size: "1.2 MB",
    thumbnail: "/grocery-receipt-image.jpg",
  },
  {
    id: "3",
    name: "Contract_draft.pdf",
    uploadDate: "2024-01-13T09:15:00Z",
    type: "pdf" as const,
    status: "completed" as const,
    size: "5.8 MB",
    thumbnail: "/contract-document-thumbnail.png",
  },
  {
    id: "4",
    name: "Business_card.png",
    uploadDate: "2024-01-12T14:20:00Z",
    type: "image" as const,
    status: "failed" as const,
    size: "0.8 MB",
    thumbnail: "/professional-business-card.png",
  },
  {
    id: "5",
    name: "Report_Q4.pdf",
    uploadDate: "2024-01-11T11:00:00Z",
    type: "pdf" as const,
    status: "completed" as const,
    size: "12.3 MB",
    thumbnail: "/quarterly-report-document.png",
  },
  {
    id: "6",
    name: "Presentation_slides.pdf",
    uploadDate: "2024-01-10T16:30:00Z",
    type: "pdf" as const,
    status: "completed" as const,
    size: "8.7 MB",
    thumbnail: "/presentation-slides-document.jpg",
  },
  {
    id: "7",
    name: "ID_document.jpg",
    uploadDate: "2024-01-09T13:45:00Z",
    type: "image" as const,
    status: "completed" as const,
    size: "2.1 MB",
    thumbnail: "/id-document-scan.jpg",
  },
  {
    id: "8",
    name: "Medical_report.pdf",
    uploadDate: "2024-01-08T08:20:00Z",
    type: "pdf" as const,
    status: "completed" as const,
    size: "4.2 MB",
    thumbnail: "/medical-report-document.jpg",
  },
]

type FilterType = "all" | "image" | "pdf"
type SortType = "newest" | "oldest" | "name" | "size"
type ViewType = "grid" | "list"

export function DocumentsContent() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filterType, setFilterType] = useState<FilterType>("all")
  const [sortType, setSortType] = useState<SortType>("newest")
  const [viewType, setViewType] = useState<ViewType>("grid")

  // Filter and sort documents
  const filteredAndSortedDocuments = mockDocuments
    .filter((doc) => {
      const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesFilter = filterType === "all" || doc.type === filterType
      return matchesSearch && matchesFilter
    })
    .sort((a, b) => {
      switch (sortType) {
        case "newest":
          return new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime()
        case "oldest":
          return new Date(a.uploadDate).getTime() - new Date(b.uploadDate).getTime()
        case "name":
          return a.name.localeCompare(b.name)
        case "size":
          const getSizeInBytes = (size: string) => {
            const [num, unit] = size.split(" ")
            const multiplier = unit === "MB" ? 1024 * 1024 : unit === "KB" ? 1024 : 1
            return Number.parseFloat(num) * multiplier
          }
          return getSizeInBytes(b.size) - getSizeInBytes(a.size)
        default:
          return 0
      }
    })

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">My Documents</h1>
          <p className="text-muted-foreground">Manage and view all your uploaded documents in one place</p>
        </div>
        <div className="flex items-center gap-2">
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
      </div>

      {/* Filters and Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center flex-1">
          {/* Search */}
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Filter */}
          <Select value={filterType} onValueChange={(value: FilterType) => setFilterType(value)}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Files</SelectItem>
              <SelectItem value="image">Images</SelectItem>
              <SelectItem value="pdf">PDFs</SelectItem>
            </SelectContent>
          </Select>

          {/* Sort */}
          <Select value={sortType} onValueChange={(value: SortType) => setSortType(value)}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest First</SelectItem>
              <SelectItem value="oldest">Oldest First</SelectItem>
              <SelectItem value="name">Name A-Z</SelectItem>
              <SelectItem value="size">Size (Large)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
          <Button
            variant={viewType === "grid" ? "default" : "ghost"}
            size="sm"
            onClick={() => setViewType("grid")}
            className="h-8 w-8 p-0"
          >
            <Grid3X3 className="w-4 h-4" />
          </Button>
          <Button
            variant={viewType === "list" ? "default" : "ghost"}
            size="sm"
            onClick={() => setViewType("list")}
            className="h-8 w-8 p-0"
          >
            <List className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Results Count */}
      <div className="text-sm text-muted-foreground">
        {filteredAndSortedDocuments.length} document{filteredAndSortedDocuments.length !== 1 ? "s" : ""} found
      </div>

      {/* Documents Grid/List */}
      {filteredAndSortedDocuments.length > 0 ? (
        <div
          className={cn(
            viewType === "grid" ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" : "space-y-4",
          )}
        >
          {filteredAndSortedDocuments.map((document) => (
            <DocumentCard key={document.id} document={document} viewType={viewType} />
          ))}
        </div>
      ) : (
        <DocumentsEmptyState
          hasSearch={searchQuery.length > 0 || filterType !== "all"}
          searchQuery={searchQuery}
          filterType={filterType}
        />
      )}
    </div>
  )
}
