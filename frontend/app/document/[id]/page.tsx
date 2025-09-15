import { AppLayout } from "@/components/layout/app-layout"
import { DocumentDetailsContent } from "@/components/document/document-details-content"

interface DocumentPageProps {
  params: {
    id: string
  }
}

export default function DocumentPage({ params }: DocumentPageProps) {
  return (
    <AppLayout>
      <DocumentDetailsContent documentId={params.id} />
    </AppLayout>
  )
}
