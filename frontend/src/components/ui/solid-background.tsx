import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface SolidBackgroundProps {
  children: ReactNode;
  className?: string;
  variant?: 'slate' | 'blue' | 'gradient';
}

export default function SolidBackground({ 
  children, 
  className,
  variant = 'slate' 
}: SolidBackgroundProps) {
  const backgrounds = {
    'slate': 'bg-slate-50',
    'blue': 'bg-blue-50',
    'gradient': 'bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50'
  };

  return (
    <div className={cn('relative min-h-screen', backgrounds[variant], className)}>
      {/* Subtle grid pattern overlay */}
      <div 
        className="absolute inset-0 opacity-[0.03]" 
        style={{
          backgroundImage: `
            linear-gradient(to right, rgb(15 23 42) 1px, transparent 1px),
            linear-gradient(to bottom, rgb(15 23 42) 1px, transparent 1px)
          `,
          backgroundSize: '64px 64px'
        }}
      />
      
      {/* Accent dots in corners */}
      <div className="absolute top-20 right-20 w-2 h-2 rounded-full bg-cyan-500 opacity-40" />
      <div className="absolute top-40 right-40 w-1.5 h-1.5 rounded-full bg-teal-500 opacity-30" />
      <div className="absolute bottom-40 left-40 w-2 h-2 rounded-full bg-blue-500 opacity-30" />
      <div className="absolute bottom-60 left-60 w-1.5 h-1.5 rounded-full bg-cyan-500 opacity-40" />
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
