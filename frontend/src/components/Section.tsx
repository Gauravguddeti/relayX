"use client"

import { motion } from "framer-motion"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import type { SectionProps } from "../types"

export default function Section({ id, title, subtitle, content, isActive, showButton, buttonText, onTestCall }: SectionProps) {
  const navigate = useNavigate()
  return (
    <section id={id} className="relative h-screen w-full snap-start flex flex-col justify-center p-8 md:p-16 lg:p-24">
      {subtitle && (
        <motion.div
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={isActive ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
        >
          {subtitle}
        </motion.div>
      )}
      <motion.h2
        className="text-4xl md:text-6xl lg:text-[5rem] xl:text-[6rem] font-bold leading-[1.1] tracking-tight max-w-4xl text-white"
        initial={{ opacity: 0, y: 50 }}
        animate={isActive ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
      >
        {title}
      </motion.h2>
      {content && (
        <motion.p
          className="text-lg md:text-xl lg:text-2xl max-w-2xl mt-6 text-neutral-400"
          initial={{ opacity: 0, y: 50 }}
          animate={isActive ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {content}
        </motion.p>
      )}
      {showButton && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isActive ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-8"
        >
          <Button
            variant="outline"
            size="lg"
            onClick={() => {
              if (id === 'hero' || id === 'join') {
                navigate('/login')
              } else if (id === 'features') {
                navigate('/pricing')
              } else if (id === 'pricing') {
                onTestCall?.()
              } else {
                onTestCall?.()
              }
            }}
            className="text-cyan-500 bg-transparent border-cyan-500 hover:bg-cyan-500 hover:text-black transition-colors"
          >
            {buttonText}
          </Button>
        </motion.div>
      )}
    </section>
  )
}
