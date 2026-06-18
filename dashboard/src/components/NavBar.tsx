import { useEffect,useState } from "react";
import { motion } from "framer-motion";
import { Activity,Github } from "lucide-react";
import clsx from "clsx";

const LINKS=[
  { id: "funnel",label: "Funnel" },
  { id: "decay",label: "Decay" },
  { id: "testing",label: "Multiple Testing" },
  { id: "pbo",label: "Overfitting" },
  { id: "regimes",label: "Regimes" },
  { id: "explorer",label: "Explorer" },
];

export default function NavBar() {
  const [scrolled,setScrolled]=useState(false);
  const [active,setActive]=useState<string>("");

  useEffect(() =>{
    const onScroll=() =>setScrolled(window.scrollY>24);
    onScroll();
    window.addEventListener("scroll",onScroll,{ passive: true });
    return () =>window.removeEventListener("scroll",onScroll);
  },[]);

  useEffect(() =>{
    const obs=new IntersectionObserver(
      (entries) =>{
        entries.forEach((e) =>{
          if (e.isIntersecting) setActive(e.target.id);
        });
      },
      { rootMargin: "-45% 0px -50% 0px" }
    );
    LINKS.forEach((l) =>{
      const el=document.getElementById(l.id);
      if (el) obs.observe(el);
    });
    return () =>obs.disconnect();
  },[]);

  return (
    <motion.header
      initial={{ y: -80,opacity: 0 }}
      animate={{ y: 0,opacity: 1 }}
      transition={{ duration: 0.6,ease: [0.16,1,0.3,1] }}
      className={clsx(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        scrolled
          ? "border-b border-line/70 bg-ink/70 backdrop-blur-xl"
          : "border-b border-transparent"
      )}
   >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5">
        <a href="#top" className="group flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-xl grad-accent shadow-glow">
            <Activity className="h-5 w-5 text-white" strokeWidth={2.5} />
          </span>
          <span className="hidden text-sm font-bold tracking-tight text-white sm:block">
            AlphaAudit
          </span>
        </a>

        <nav className="hidden items-center gap-1 md:flex">
          {LINKS.map((l) =>(
            <a
              key={l.id}
              href={`#${l.id}`}
              className={clsx(
                "relative rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active===l.id
                  ? "text-white"
                  : "text-sub hover:text-slate-200"
              )}
           >
              {active===l.id && (
                <motion.span
                  layoutId="nav-pill"
                  className="absolute inset-0 -z-10 rounded-lg bg-panel2/80 ring-1 ring-line"
                  transition={{ type: "spring",stiffness: 380,damping: 30 }}
                />
              )}
              {l.label}
            </a>
          ))}
        </nav>

        <a
          href="https://github.com/bhavishy2801/AlphaAudit"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 rounded-lg border border-line bg-panel2/60 px-3 py-2 text-sm font-medium text-slate-200 transition-colors hover:border-accent/60 hover:text-white"
       >
          <Github className="h-4 w-4" />
          <span className="hidden sm:block">Repo</span>
        </a>
      </div>
    </motion.header>
  );
}
