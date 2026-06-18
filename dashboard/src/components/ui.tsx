import { motion } from "framer-motion";
import clsx from "clsx";
import type { ReactNode } from "react";

/** Section wrapper with a scroll anchor and a staggered fade-up reveal. */
export function Section({
  id,
  children,
  className,
}: {
  id?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      id={id}
      className={clsx("mx-auto w-full max-w-7xl px-5 py-14 md:py-20",className)}
   >
      {children}
    </section>
  );
}

export function Reveal({
  children,
  delay=0,
  className,
  y=24,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  y?: number;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0,y }}
      whileInView={{ opacity: 1,y: 0 }}
      viewport={{ once: true,margin: "-12% 0px" }}
      transition={{ duration: 0.7,delay,ease: [0.16,1,0.3,1] }}
   >
      {children}
    </motion.div>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  blurb,
}: {
  eyebrow: string;
  title: string;
  blurb?: string;
}) {
  return (
    <div className="mb-9 max-w-3xl">
      <Reveal>
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-line/80 bg-panel2/50 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-accent2">
          <span className="h-1.5 w-1.5 rounded-full bg-accent2 shadow-glowcyan" />
          {eyebrow}
        </div>
      </Reveal>
      <Reveal delay={0.05}>
        <h2 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">
          {title}
        </h2>
      </Reveal>
      {blurb && (
        <Reveal delay={0.1}>
          <p className="mt-3 text-[15px] leading-relaxed text-sub">{blurb}</p>
        </Reveal>
      )}
    </div>
  );
}

export function Card({
  children,
  className,
  glow,
}: {
  children: ReactNode;
  className?: string;
  glow?: boolean;
}) {
  return (
    <div
      className={clsx(
        "card p-5 transition-shadow duration-300",
        glow && "hover:shadow-glow",
        className
      )}
   >
      {children}
    </div>
  );
}

export function Chip({
  children,
  color,
  bg,
}: {
  children: ReactNode;
  color?: string;
  bg?: string;
}) {
  return (
    <span
      className="chip"
      style={{
        color: color ?? "#cbd5e1",
        background: bg ?? "rgba(148,163,184,0.12)",
      }}
   >
      {children}
    </span>
  );
}

export function Stat({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  accent?: string;
}) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-sub">{label}</div>
      <div
        className="tnum mt-1 text-2xl font-bold text-white"
        style={accent ? { color: accent } : undefined}
     >
        {value}
      </div>
      {sub && <div className="mt-0.5 text-xs text-sub">{sub}</div>}
    </div>
  );
}
