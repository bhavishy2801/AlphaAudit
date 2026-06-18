import { motion } from "framer-motion";
import { AlertTriangle,Loader2 } from "lucide-react";
import { useResults } from "./hooks/useResults";
import NavBar from "./components/NavBar";
import Hero from "./components/Hero";
import FunnelSection from "./components/FunnelSection";
import DecaySection from "./components/DecaySection";
import MultipleTestingSection from "./components/MultipleTestingSection";
import PBOSection from "./components/PBOSection";
import RegimeSection from "./components/RegimeSection";
import ExplorerSection from "./components/ExplorerSection";
import Footer from "./components/Footer";

export default function App() {
  const { data,loading,error }=useResults();

  return (
    <div className="relative min-h-screen">
      <div className="bg-field" />
      <div className="bg-grid" />
      <NavBar />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} />}

      {data && (
        <main>
          <Hero data={data} />
          <FunnelSection data={data} />
          <DecaySection data={data} />
          <MultipleTestingSection data={data} />
          <PBOSection data={data} />
          <RegimeSection data={data} />
          <ExplorerSection data={data} />
          <Footer data={data} />
        </main>
      )}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="grid min-h-screen place-items-center">
      <motion.div
        initial={{ opacity: 0,scale: 0.95 }}
        animate={{ opacity: 1,scale: 1 }}
        className="flex flex-col items-center gap-4 text-sub"
     >
        <Loader2 className="h-8 w-8 animate-spin text-accent" />
        <p className="text-sm">Loading audit results…</p>
      </motion.div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="grid min-h-screen place-items-center px-5">
      <div className="card max-w-lg p-8 text-center">
        <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-xl bg-bad/15 text-bad">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-bold text-white">No results found</h2>
        <p className="mt-2 text-sm text-sub">{message}</p>
        <pre className="mt-4 overflow-x-auto rounded-lg border border-line bg-ink/60 px-4 py-3 text-left text-xs text-accent2">
          python run_all.py
        </pre>
      </div>
    </div>
  );
}
