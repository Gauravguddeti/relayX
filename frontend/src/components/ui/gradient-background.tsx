import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface GradientBackgroundProps {
  children: ReactNode;
  className?: string;
  variant?: 'purple-blue' | 'cyan-pink' | 'violet-indigo';
}

export default function GradientBackground({ 
  children, 
  className,
  variant = 'purple-blue' 
}: GradientBackgroundProps) {
  const gradients = {
    'purple-blue': 'from-slate-50 via-blue-50 to-cyan-50',
    'cyan-pink': 'from-cyan-50 via-teal-50 to-emerald-50',
    'violet-indigo': 'from-blue-50 via-cyan-50 to-teal-50'
  };

  return (
    <div className={cn('relative overflow-hidden', className)}>
      {/* Animated gradient background */}
      <div className={cn(
        'absolute inset-0 bg-gradient-to-br animate-gradient',
        gradients[variant]
      )} />
      
      {/* Grain texture overlay */}
      <div className="absolute inset-0 opacity-[0.015]" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='4' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' /%3E%3C/svg%3E")`,
        backgroundRepeat: 'repeat',
        backgroundSize: '128px'
      }} />
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
