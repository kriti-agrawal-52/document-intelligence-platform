"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { StatusBadge } from "@/components/ui/status-badge"
import { FileTypeBadge } from "@/components/ui/file-type-badge"
import { QuickUploadZone } from "@/components/dashboard/quick-upload-zone"
import { ImageIcon, FileText, Eye, Trash2 } from "lucide-react"
import Link from "next/link"

// Mock data for recent documents
const recentDocuments = [
  {
    id: "1",
    name: "Invoice_2024_001.pdf",
    uploadDate: "2024-01-15",
    type: "pdf" as const,
    status: "completed" as const,
    size: "2.4 MB",
  },
  {
    id: "2",
    name: "Receipt_grocery.jpg",
    uploadDate: "2024-01-14",
    type: "image" as const,
    status: "processing" as const,
    size: "1.2 MB",
  },
  {
    id: "3",
    name: "Contract_draft.pdf",
    uploadDate: "2024-01-13",
    type: "pdf" as const,
    status: "completed" as const,
    size: "5.8 MB",
  },
  {
    id: "4",
    name: "Business_card.png",
    uploadDate: "2024-01-12",
    type: "image" as const,
    status: "failed" as const,
    size: "0.8 MB",
  },
  {
    id: "5",
    name: "Report_Q4.pdf",
    uploadDate: "2024-01-11",
    type: "pdf" as const,
    status: "completed" as const,
    size: "12.3 MB",
  },
]

export function DashboardContent() {
  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-foreground">Welcome back, John!</h1>
        <p className="text-muted-foreground">
          Transform your documents with AI-powered intelligence. Upload, process, and analyze your files seamlessly.
        </p>
      </div>

      {/* Quick Upload Zones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuickUploadZone
          type="images"
          title="Upload Images"
          description="PNG, JPG, JPEG supported"
          icon={<ImageIcon className="w-8 h-8" />}
          href="/upload/images"
        />
        <QuickUploadZone
          type="pdf"
          title="Upload PDF"
          description="PDF files up to 10MB, max 20 pages"
          icon={<FileText className="w-8 h-8" />}
          href="/upload/pdf"
        />
      </div>

      {/* Recent Documents Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="text-xl">Recent Documents</CardTitle>
            <CardDescription>Your latest uploaded and processed documents</CardDescription>
          </div>
          <Button asChild variant="outline">
            <Link href="/documents">View All</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {recentDocuments.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Upload Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentDocuments.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell className="font-medium">{doc.name}</TableCell>
                      <TableCell>{new Date(doc.uploadDate).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <FileTypeBadge type={doc.type} size="sm" />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={doc.status} size="sm" />
                      </TableCell>
                      <TableCell className="text-muted-foreground">{doc.size}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button asChild variant="ghost" size="sm">
                            <Link href={`/document/${doc.id}`}>
                              <Eye className="w-4 h-4" />
                            </Link>
                          </Button>
                          <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">No documents yet</h3>
              <p className="text-muted-foreground mb-6">Start by uploading your first document to get started.</p>
              <div className="flex items-center justify-center gap-4">
                <Button asChild>
                  <Link href="/upload/images">Upload Images</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/upload/pdf">Upload PDF</Link>
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground">+3 from last week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Images Processed</CardTitle>
            <ImageIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">16</div>
            <p className="text-xs text-muted-foreground">+2 from last week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">PDFs Analyzed</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8</div>
            <p className="text-xs text-muted-foreground">+1 from last week</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
