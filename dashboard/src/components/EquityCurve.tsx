import { useMemo,useState } from "react";
import { motion } from "framer-motion";
import type { Anomaly } from "../types";

/**
*Cumulative log-equity curve with the in-sample/out-of-sample split shaded.
*Pure SVG so it animates its draw-in and stays crisp at any size.
 */
export default function EquityCurve({
  anomaly,
  dates,
  height=220,
}: {
  anomaly: Anomaly;
  dates: string[];
  height?: number;
}) {
  const W=640;
  const H=height;
  const padX=6;
  const padY=16;
  const curve=anomaly.equity_curve;
  const [hoverIdx,setHoverIdx]=useState<number | null>(null);

  const { path,areaPath,pts,yMin,yMax,splitX }=useMemo(() =>{
    const n=curve.length;
    const yMin=Math.min(...curve,0);
    const yMax=Math.max(...curve,0.05);
    const sx=(i: number) =>padX + (i/(n-1))*(W-2*padX);
    const sy=(v: number) =>
      padY + (1-(v-yMin)/(yMax-yMin || 1))*(H-2*padY);
    const pts=curve.map((v,i) =>[sx(i),sy(v)] as [number,number]);
    const path=pts.map((p,i) =>`${i ? "L" : "M"} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
    const base=sy(yMin);
    const areaPath=`${path} L ${pts[n-1][0].toFixed(1)} ${base} L ${pts[0][0].toFixed(1)} ${base} Z`;
    const splitX=sx(Math.max(0,Math.min(n-1,anomaly.pub_index)));
    return { path,areaPath,pts,yMin,yMax,splitX };
  },[curve,anomaly.pub_index,H]);

  const zeroY =
    padY + (1-(0-yMin)/(yMax-yMin || 1))*(H-2*padY);

  const onMove=(e: React.MouseEvent<SVGSVGElement>) =>{
    const rect=e.currentTarget.getBoundingClientRect();
    const x=((e.clientX-rect.left)/rect.width)*W;
    const i=Math.round(((x-padX)/(W-2*padX))*(curve.length-1));
    setHoverIdx(Math.max(0,Math.min(curve.length-1,i)));
  };

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        onMouseMove={onMove}
        onMouseLeave={() =>setHoverIdx(null)}
        preserveAspectRatio="none"
     >
        <defs>
          <linearGradient id="eqfill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#6366F1" stopOpacity="0.35" />
            <stop offset="1" stopColor="#6366F1" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="eqstroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#22D3EE" />
            <stop offset="1" stopColor="#818CF8" />
          </linearGradient>
        </defs>

        {/* OOS region shading */}
        <rect x={splitX} y={0} width={W-splitX} height={H} fill="#F59E0B" opacity="0.06" />
        <line x1={splitX} y1={0} x2={splitX} y2={H} stroke="#F59E0B" strokeWidth="1.2" strokeDasharray="4 4" opacity="0.8" />

        {/* zero baseline */}
        <line x1={padX} y1={zeroY} x2={W-padX} y2={zeroY} stroke="#2A3350" strokeWidth="1" />

        <path d={areaPath} fill="url(#eqfill)" />
        <motion.path
          d={path}
          fill="none"
          stroke="url(#eqstroke)"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          whileInView={{ pathLength: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1.6,ease: "easeInOut" }}
          vectorEffect="non-scaling-stroke"
        />

        {hoverIdx!==null && (
          <g>
            <line
              x1={pts[hoverIdx][0]}
              y1={0}
              x2={pts[hoverIdx][0]}
              y2={H}
              stroke="#94A3B8"
              strokeWidth="1"
              opacity="0.4"
            />
            <circle cx={pts[hoverIdx][0]} cy={pts[hoverIdx][1]} r="3.5" fill="#fff" stroke="#6366F1" strokeWidth="2" />
          </g>
        )}
      </svg>

      {/* labels */}
      <div className="pointer-events-none absolute left-2 top-1 text-[10px] font-medium text-accent2">
        in-sample
      </div>
      <div
        className="pointer-events-none absolute top-1 text-[10px] font-medium text-warn"
        style={{ left: `${(splitX/W)*100 + 1}%` }}
     >
        out-of-sample →
      </div>

      {hoverIdx!==null && (
        <div className="mt-1 flex items-center justify-between text-[11px] text-sub">
          <span>{dates[hoverIdx] ?? ""}</span>
          <span className="tnum font-mono text-slate-300">
            cum. log-equity {curve[hoverIdx].toFixed(3)}
          </span>
        </div>
      )}
    </div>
  );
}
