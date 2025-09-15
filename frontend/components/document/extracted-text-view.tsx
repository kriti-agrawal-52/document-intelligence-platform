"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Copy, Search, Check } from "lucide-react"

interface ExtractedTextViewProps {
  text: string
  wordCount: number
  characterCount: number
}

export function ExtractedTextView({ text, wordCount, characterCount }: ExtractedTextViewProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy text:", err)
    }
  }

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text

    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi")
    return text.replace(regex, "<mark class='bg-yellow-200 dark:bg-yellow-800'>$1</mark>")
  }

  return (
    <div className="space-y-4">
      {/* Text Statistics */}
      <div className="flex items-center gap-4">
        <Badge variant="secondary">{wordCount} words</Badge>
        <Badge variant="secondary">{characterCount} characters</Badge>
      </div>

      {/* Search and Copy Controls */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            placeholder="Search within text..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline" onClick={handleCopy}>
          {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
          {copied ? "Copied!" : "Copy"}
        </Button>
      </div>

      {/* Extracted Text */}
      <div className="border rounded-lg p-4 bg-muted/30 max-h-96 overflow-y-auto">
        <pre
          className="whitespace-pre-wrap text-sm font-mono leading-relaxed"
          dangerouslySetInnerHTML={{
            __html: highlightText(text, searchQuery),
          }}
        />
      </div>
    </div>
  )
}
