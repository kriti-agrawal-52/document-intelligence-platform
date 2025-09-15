import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, XCircle, Loader2 } from "lucide-react"

interface StatusBadgeProps {
  status: "processing" | "completed" | "failed"
  size?: "sm" | "md" | "lg"
  className?: string
}

export function StatusBadge({ status, size = "md", className }: StatusBadgeProps) {
  const variants = {
    processing: {
      className: "bg-warning/10 text-warning border-warning/20",
      icon: <Loader2 className="w-3 h-3 animate-spin" />,
      text: "Processing",
    },
    completed: {
      className: "bg-success/10 text-success border-success/20",
      icon: <CheckCircle className="w-3 h-3" />,
      text: "Completed",
    },
    failed: {
      className: "bg-destructive/10 text-destructive border-destructive/20",
      icon: <XCircle className="w-3 h-3" />,
      text: "Failed",
    },
  }

  const sizeClasses = {
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-2",
  }

  const variant = variants[status]

  return (
    <Badge
      className={cn("inline-flex items-center gap-1.5 font-medium", variant.className, sizeClasses[size], className)}
    >
      {variant.icon}
      {variant.text}
    </Badge>
  )
}
