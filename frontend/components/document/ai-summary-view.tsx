"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Copy, Check, Sparkles } from "lucide-react"

interface AiSummaryViewProps {
  summary: string
}

export function AiSummaryView({ summary }: AiSummaryViewProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(summary)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy summary:", err)
    }
  }

  return (
    <div className="space-y-4">
      {/* Summary Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          <Badge variant="secondary">AI Generated</Badge>
        </div>
        <Button variant="outline" onClick={handleCopy}>
          {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
          {copied ? "Copied!" : "Copy"}
        </Button>
      </div>

      {/* AI Summary */}
      <div className="border rounded-lg p-4 bg-muted/30 max-h-96 overflow-y-auto">
        <div
          className="prose prose-sm max-w-none dark:prose-invert"
          dangerouslySetInnerHTML={{
            __html: summary.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br />"),
          }}
        />
      </div>

      {/* Summary Note */}
      <p className="text-xs text-muted-foreground">
        Summary generated automatically using AI. Please verify important details with the original document.
      </p>
    </div>
  )
}
