import { cn } from '@/lib/utils'

interface Props extends React.HTMLAttributes<HTMLDivElement> {}

export function Skeleton({ className, ...props }: Props) {
  return (
    <div
      className={cn('rounded-md rg-skeleton', className)}
      {...props}
    />
  )
}