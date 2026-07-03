import { cn, scoreColor, scoreLabel } from "@/lib/utils";

export function RelevanceScore({ score, size = "md" }: { score: number; size?: "sm" | "md" }) {
  const pct = Math.min(100, Math.max(0, score * 100));
  const dim = size === "sm" ? "h-10 w-10 text-xs" : "h-14 w-14 text-sm";
  const r = size === "sm" ? 16 : 22;
  const circ = 2 * Math.PI * r;

  return (
    <div className={cn("relative flex shrink-0 items-center justify-center", dim)}>
      <svg className="-rotate-90" width={size === "sm" ? 40 : 56} height={size === "sm" ? 40 : 56}>
        <circle
          cx={size === "sm" ? 20 : 28}
          cy={size === "sm" ? 20 : 28}
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          className="text-muted"
        />
        <circle
          cx={size === "sm" ? 20 : 28}
          cy={size === "sm" ? 20 : 28}
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeDasharray={circ}
          strokeDashoffset={circ - (pct / 100) * circ}
          strokeLinecap="round"
          className={scoreColor(score)}
        />
      </svg>
      <span className={cn("absolute font-mono font-semibold", scoreColor(score))}>
        {scoreLabel(score)}
      </span>
    </div>
  );
}
