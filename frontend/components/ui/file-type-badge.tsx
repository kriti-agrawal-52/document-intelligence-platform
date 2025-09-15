import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { ImageIcon, FileText } from "lucide-react"

interface FileTypeBadgeProps {
  type: "image" | "pdf"
  size?: "sm" | "md" | "lg"
  className?: string
}

export function FileTypeBadge({ type, size = "md", className }: FileTypeBadgeProps) {
  const variants = {
    image: {
      className: "bg-info/10 text-info border-info/20",
      icon: <ImageIcon className="w-3 h-3" />,
      text: "Image",
    },
    pdf: {
      className: "bg-destructive/10 text-destructive border-destructive/20",
      icon: <FileText className="w-3 h-3" />,
      text: "PDF",
    },
  }

  const sizeClasses = {
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-2",
  }

  const variant = variants[type]

  return (
    <Badge
      className={cn("inline-flex items-center gap-1.5 font-medium", variant.className, sizeClasses[size], className)}
    >
      {variant.icon}
      {variant.text}
    </Badge>
  )
}
