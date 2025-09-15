"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StatusBadge } from "@/components/ui/status-badge"
import { FileTypeBadge } from "@/components/ui/file-type-badge"
import { DocumentPreview } from "@/components/document/document-preview"
import { ExtractedTextView } from "@/components/document/extracted-text-view"
import { AiSummaryView } from "@/components/document/ai-summary-view"
import { Download, Trash2, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"

// Mock document data
const mockDocument = {
  id: "1",
  name: "Invoice_2024_001.pdf",
  uploadDate: "2024-01-15T10:30:00Z",
  type: "pdf" as const,
  status: "completed" as const,
  size: "2.4 MB",
  dimensions: "8.5 × 11 in",
  pageCount: 3,
  thumbnail: "/invoice-document-preview.jpg",
  extractedText: `INVOICE

Invoice #: INV-2024-001
Date: January 15, 2024
Due Date: February 15, 2024

Bill To:
Acme Corporation
123 Business Street
New York, NY 10001

From:
Professional Services LLC
456 Service Avenue
Los Angeles, CA 90210

Description                    Qty    Rate      Amount
Web Development Services        40    $150.00   $6,000.00
UI/UX Design Consultation      20    $120.00   $2,400.00
Project Management             10    $100.00   $1,000.00

                              Subtotal: $9,400.00
                                   Tax: $752.00
                                 Total: $10,152.00

Payment Terms: Net 30 days
Thank you for your business!`,
  aiSummary: `This is a professional services invoice (INV-2024-001) dated January 15, 2024, from Professional Services LLC to Acme Corporation. 

**Key Details:**
- **Total Amount:** $10,152.00 (including $752.00 tax)
- **Due Date:** February 15, 2024
- **Payment Terms:** Net 30 days

**Services Provided:**
- Web Development Services: 40 hours at $150/hour = $6,000
- UI/UX Design Consultation: 20 hours at $120/hour = $2,400  
- Project Management: 10 hours at $100/hour = $1,000

**Parties:**
- **Vendor:** Professional Services LLC, Los Angeles, CA
- **Client:** Acme Corporation, New York, NY

This appears to be a legitimate business invoice for technology consulting services with standard payment terms.`,
  wordCount: 87,
  characterCount: 542,
}

interface DocumentDetailsContentProps {
  documentId: string
}

export function DocumentDetailsContent({ documentId }: DocumentDetailsContentProps) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState("text")

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const handleDelete = () => {
    // In a real app, show confirmation dialog and delete
    console.log("Delete document:", documentId)
    router.push("/documents")
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/documents" className="hover:text-foreground">
          Documents
        </Link>
        <span>/</span>
        <span className="text-foreground">{mockDocument.name}</span>
      </div>

      {/* Header Section */}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/documents">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Documents
              </Link>
            </Button>
          </div>
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-foreground text-balance">{mockDocument.name}</h1>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>Uploaded {formatDate(mockDocument.uploadDate)}</span>
              <span>•</span>
              <span>{mockDocument.size}</span>
              {mockDocument.pageCount && (
                <>
                  <span>•</span>
                  <span>
                    {mockDocument.pageCount} page{mockDocument.pageCount !== 1 ? "s" : ""}
                  </span>
                </>
              )}
            </div>
            <div className="flex items-center gap-2">
              <FileTypeBadge type={mockDocument.type} />
              <StatusBadge status={mockDocument.status} />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
          <Button
            variant="outline"
            onClick={handleDelete}
            className="text-destructive hover:text-destructive bg-transparent"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column - Document Preview */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Document Preview</CardTitle>
            </CardHeader>
            <CardContent>
              <DocumentPreview document={mockDocument} />
            </CardContent>
          </Card>

          {/* File Information */}
          <Card>
            <CardHeader>
              <CardTitle>File Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">File Size</span>
                  <p className="font-medium">{mockDocument.size}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Upload Date</span>
                  <p className="font-medium">{formatDate(mockDocument.uploadDate)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">File Type</span>
                  <p className="font-medium">{mockDocument.type.toUpperCase()}</p>
                </div>
                {mockDocument.pageCount && (
                  <div>
                    <span className="text-muted-foreground">Pages</span>
                    <p className="font-medium">{mockDocument.pageCount}</p>
                  </div>
                )}
                {mockDocument.dimensions && (
                  <div>
                    <span className="text-muted-foreground">Dimensions</span>
                    <p className="font-medium">{mockDocument.dimensions}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Results */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>AI Analysis Results</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="text">Extracted Text</TabsTrigger>
                  <TabsTrigger value="summary">AI Summary</TabsTrigger>
                </TabsList>
                <TabsContent value="text" className="mt-6">
                  <ExtractedTextView
                    text={mockDocument.extractedText}
                    wordCount={mockDocument.wordCount}
                    characterCount={mockDocument.characterCount}
                  />
                </TabsContent>
                <TabsContent value="summary" className="mt-6">
                  <AiSummaryView summary={mockDocument.aiSummary} />
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
