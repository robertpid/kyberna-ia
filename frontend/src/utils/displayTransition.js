import { useEffect, useRef, useState } from "react";

let supportsDisplayTransitionCache;

/**
 * Detecta soporte real de transiciones discretas en `display` evitando el falso
 * positivo de `CSS.supports('transition-behavior', 'allow-discrete')` en Firefox.
 */
export function canTransitionDisplay() {
  if (supportsDisplayTransitionCache !== undefined) {
    return supportsDisplayTransitionCache;
  }
  if (
    typeof window === "undefined" ||
    !window.CSS?.supports?.("transition-behavior", "allow-discrete") ||
    !document.body
  ) {
    return false;
  }
  const probe = document.createElement("div");
  probe.style.cssText =
    "transition: display 1s allow-discrete !important; display: block;";
  document.body.appendChild(probe);
  getComputedStyle(probe).display;
  probe.style.display = "none";
  supportsDisplayTransitionCache = getComputedStyle(probe).display === "block";
  probe.remove();
  return supportsDisplayTransitionCache;
}

/**
 * Controla visibilidad animada de entrada y salida usando `[hidden]` y el
 * atributo `[data-closing]` como fallback cuando `display` no es transicionable.
 */
export function useAnimatedVisibility(isOpen) {
  const elementRef = useRef(null);
  const [isHidden, setIsHidden] = useState(!isOpen);
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const el = elementRef.current;

    if (isOpen) {
      setIsClosing(false);
      setIsHidden(false);
      return undefined;
    }

    if (!el || isHidden) {
      setIsHidden(true);
      return undefined;
    }

    const runExit = async () => {
      if (canTransitionDisplay()) {
        setIsHidden(true);
        return;
      }

      setIsClosing(true);
      await new Promise((resolve) => requestAnimationFrame(resolve));
      if (cancelled || !elementRef.current) {
        return;
      }

      const animations = elementRef.current.getAnimations?.() || [];
      if (animations.length > 0) {
        await Promise.race([
          Promise.allSettled(animations.map((anim) => anim.finished)),
          new Promise((resolve) => setTimeout(resolve, 450)),
        ]);
      }

      if (!cancelled) {
        setIsClosing(false);
        setIsHidden(true);
      }
    };

    runExit();
    return () => {
      cancelled = true;
    };
  }, [isOpen, isHidden]);

  return { elementRef, isHidden, isClosing };
}

/**
 * Interpola numéricamente métricas clave respetando `prefers-reduced-motion`.
 */
export function useAnimatedNumber(targetValue, durationMs = 520, pauseMotion = false) {
  const [displayValue, setDisplayValue] = useState(targetValue);
  const previousRef = useRef(targetValue);

  useEffect(() => {
    const prefersReduced =
      pauseMotion ||
      (typeof window !== "undefined" &&
        window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);

    if (prefersReduced) {
      previousRef.current = targetValue;
      setDisplayValue(targetValue);
      return undefined;
    }

    const startValue = previousRef.current;
    const delta = targetValue - startValue;
    if (Math.abs(delta) < 0.05) {
      previousRef.current = targetValue;
      setDisplayValue(targetValue);
      return undefined;
    }

    let rafId = 0;
    const startTime = performance.now();

    const tick = (now) => {
      const elapsed = now - startTime;
      const t = Math.min(1, elapsed / durationMs);
      const eased = 1 - (1 - t) ** 3;
      const current = startValue + delta * eased;
      setDisplayValue(current);

      if (t < 1) {
        rafId = requestAnimationFrame(tick);
      } else {
        previousRef.current = targetValue;
      }
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [targetValue, durationMs, pauseMotion]);

  return displayValue;
}

