import { cn } from '@/lib/utils';

interface FloatingShapesProps {
  className?: string;
  density?: 'low' | 'medium' | 'high';
}

export default function FloatingShapes({ className, density = 'medium' }: FloatingShapesProps) {
  const counts = { low: 3, medium: 5, high: 8 };
  const count = counts[density];

  return (
    <div className={cn('absolute inset-0 overflow-hidden pointer-events-none', className)}>
      {Array.from({ length: count }).map((_, i) => {
        const size = 100 + Math.random() * 300;
        const delay = Math.random() * 5;
        const duration = 15 + Math.random() * 15;
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        
        return (
          <div
            key={i}
            className="absolute rounded-full blur-3xl opacity-20"
            style={{
              width: `${size}px`,
              height: `${size}px`,
              left: `${x}%`,
              top: `${y}%`,
              background: i % 3 === 0 
                ? 'linear-gradient(135deg, #0891b2 0%, #0ea5e9 100%)'
                : i % 3 === 1
                ? 'linear-gradient(135deg, #10b981 0%, #14b8a6 100%)'
                : 'linear-gradient(135deg, #1e40af 0%, #0891b2 100%)',
              animation: `float ${duration}s ease-in-out infinite`,
              animationDelay: `${delay}s`,
            }}
          />
        );
      })}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translate(0, 0) scale(1); }
          25% { transform: translate(10px, -15px) scale(1.05); }
          50% { transform: translate(-5px, -25px) scale(0.95); }
          75% { transform: translate(-15px, -10px) scale(1.02); }
        }
      `}</style>
    </div>
  );
}
