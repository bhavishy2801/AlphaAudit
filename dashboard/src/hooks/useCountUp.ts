import { useEffect,useRef,useState } from "react";
import { animate,useInView } from "framer-motion";

/**
*Animate a number from 0->`to` once it scrolls into view.
*Returns the live value and a ref to attach to the element.
 */
export function useCountUp(to: number,duration=1.4,decimals=0) {
  const ref=useRef<HTMLSpanElement>(null);
  const inView=useInView(ref,{ once: true,margin: "-10% 0px" });
  const [value,setValue]=useState(0);

  useEffect(() =>{
    if (!inView) return;
    const controls=animate(0,to,{
      duration,
      ease: [0.16,1,0.3,1],
      onUpdate: (v) =>setValue(Number(v.toFixed(decimals))),
    });
    return () =>controls.stop();
  },[inView,to,duration,decimals]);

  return { ref,value };
}
