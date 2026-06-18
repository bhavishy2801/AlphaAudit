import { useEffect,useState } from "react";
import type { Results } from "../types";

interface State {
  data: Results | null;
  error: string | null;
  loading: boolean;
}

/**
*Load results.json (written by the Python pipeline into /public). Falling back
*to a relative path keeps it working under Vite's `base: "./"` static build.
 */
export function useResults(): State {
  const [state,setState]=useState<State>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() =>{
    let cancelled=false;
    const urls=["./results.json","/results.json"];

    (async () =>{
      for (const url of urls) {
        try {
          const res=await fetch(url,{ cache: "no-cache" });
          if (!res.ok) continue;
          const json=(await res.json()) as Results;
          if (!cancelled) setState({ data: json,error: null,loading: false });
          return;
        } catch {
          /* try next url */
        }
      }
      if (!cancelled)
        setState({
          data: null,
          loading: false,
          error:
            "Could not load results.json. Run `python run_all.py` from the project root to generate it.",
        });
    })();

    return () =>{
      cancelled=true;
    };
  },[]);

  return state;
}
