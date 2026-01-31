import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export default function GlassCard({ children, className, hover = true }: GlassCardProps) {
  return (
    <div className={cn(
      'backdrop-blur-xl bg-white/40 dark:bg-gray-900/40',
      'border border-white/20 dark:border-gray-700/30',
      'rounded-2xl shadow-xl',
      'transition-all duration-300',
      hover && 'hover:bg-white/60 dark:hover:bg-gray-900/60 hover:shadow-2xl hover:scale-[1.02]',
      className
    )}>
      {children}
    </div>
  );
}
