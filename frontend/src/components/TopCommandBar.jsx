import React, { useEffect, useState } from "react";
import { useAnimatedVisibility } from "../utils/displayTransition.js";

/**
 * Barra superior de comando con el Pipeline Autónomo de 4 Etapas:
 * 1. Polling meteorológico de 15 minutos (Vigilancia normal)
 * 2. Detección de anomalías multifactoriales y disparo del modelo ML
 * 3. Web Scraping de noticias regionales y redes ante lluvia intensa en <= 4h
 * 4. Acción humanitaria (cálculo de damnificados, recomendaciones y desvío vial Dijkstra)
 */
export default function TopCommandBar({
  decision,
  isBusy,
  autoPolling,
  animationsPaused,
  onSetScenario,
  onSelectStage,
  onTestFakeNewsScenario,
  onTogglePolling,
  onToggleAnimations,
  onOpenTelegramModal,
  onFocusEmergencyMap,
}) {
  const isRedAlert = decision.current_system_state === "ALERTA ROJA";
  const currentStage = decision.current_stage || "ETAPA 1 · VIGILANCIA RUTINARIA (POLLING 15 MIN)";
  const impact = decision.humanitarian_impact;
  const mlPred = decision.ml_prediction;
  const { elementRef, isHidden, isClosing } = useAnimatedVisibility(isRedAlert);

  // Contador regresivo en vivo del ciclo de Polling de 15 minutos (900 segundos)
  const [secondsRemaining, setSecondsRemaining] = useState(
    decision.next_polling_seconds_remaining || 872
  );

  useEffect(() => {
    const timer = window.setInterval(() => {
      setSecondsRemaining((prev) => (prev > 1 ? prev - 1 : 900));
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const formatCountdown = (totalSec) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const isStage1 = currentStage.includes("ETAPA 1");
  const isStage2 = currentStage.includes("ETAPA 2");
  const isStage3 = currentStage.includes("ETAPA 3");
  const isStage4 = currentStage.includes("ETAPA 4");

  return (
    <>
      <header className="topbar">
        <div className="brand-group">
          <span className="brand-emblem" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
              <path
                fill="currentColor"
                d="M12 2L2 7l10 5 10-5-10-5zm0 7.5l-6.5-3.25L12 3l6.5 3.25L12 9.5zm-8 4.25l8 4 8-4v2.5l-8 4-8-4v-2.5zm0 4.5l8 4 8-4v2.5l-8 4-8-4v-2.5z"
              />
            </svg>
          </span>
          <div>
            <h1 id="main-heading" tabIndex={-1}>
              Kyberna IA · Centro de Mando Logístico
            </h1>
            <p className="subtitle">
              Prevención y Desvío Humanitario ante el Fenómeno del Niño · Cuenca Río Moche (La Libertad)
            </p>
          </div>
        </div>

        <div
          className="status-banner"
          data-alert-active={isRedAlert ? "true" : "false"}
        >
          <span className="pulse-dot" aria-hidden="true" />
          <div>
            <span className="status-caption">Estado del Corredor</span>
            <strong className="status-value">
              {decision.current_system_state}
            </strong>
          </div>
        </div>

        <div className="topbar-actions">
          <button
            type="button"
            className="btn"
            disabled={isBusy}
            onClick={onTestFakeNewsScenario}
          >
            Filtro NLP Fake News
          </button>
          <button
            type="button"
            className={`btn ${autoPolling ? "btn-primary" : ""}`}
            aria-pressed={autoPolling}
            onClick={onTogglePolling}
          >
            {autoPolling ? "Auto-Sync: ON" : "Auto-Sync: OFF"}
          </button>
          <button
            type="button"
            className="btn"
            aria-pressed={animationsPaused}
            onClick={onToggleAnimations}
          >
            {animationsPaused ? "Reanudar Animación" : "Pausar Animación"}
          </button>
          <button
            type="button"
            className="btn btn-accent"
            onClick={onOpenTelegramModal}
          >
            Bot Telegram Real
          </button>
        </div>
      </header>

      {/* Ribbon Interactivo del Pipeline Autónomo de 4 Etapas */}
      <nav className="pipeline-stepper" aria-label="Pipeline de 4 etapas de Kyberna IA">
        <div
          className={`pipeline-step ${isStage1 ? "pipeline-step-active" : ""}`}
        >
          <button
            type="button"
            className="pipeline-step-btn"
            disabled={isBusy}
            onClick={() => onSelectStage("etapa_1")}
          >
            <span className="step-badge">1</span>
            <div className="step-text">
              <span className="step-title">Polling Meteorológico</span>
              <span className="step-subtitle">
                Revisión c/15 min · Próx: <strong>{formatCountdown(secondsRemaining)}</strong>
              </span>
            </div>
          </button>
        </div>

        <div
          className={`pipeline-step ${isStage2 ? "pipeline-step-active" : ""}`}
        >
          <button
            type="button"
            className="pipeline-step-btn"
            disabled={isBusy}
            onClick={() => onSelectStage("etapa_2")}
          >
            <span className="step-badge">2</span>
            <div className="step-text">
              <span className="step-title">Anomalía + Modelo ML</span>
              <span className="step-subtitle">
                Aviso Preventivo No Alarmista
              </span>
            </div>
          </button>
        </div>

        <div
          className={`pipeline-step ${isStage3 ? "pipeline-step-active" : ""}`}
        >
          <button
            type="button"
            className="pipeline-step-btn"
            disabled={isBusy}
            onClick={() => onSelectStage("etapa_3")}
          >
            <span className="step-badge">3</span>
            <div className="step-text">
              <span className="step-title">Web Scraping en Vivo</span>
              <span className="step-subtitle">
                Prensa & Redes (Lluvias ≤ 4h)
              </span>
            </div>
          </button>
        </div>

        <div
          className={`pipeline-step ${isStage4 ? "pipeline-step-active" : ""}`}
        >
          <button
            type="button"
            className="pipeline-step-btn"
            disabled={isBusy}
            onClick={() => onSelectStage("etapa_4")}
          >
            <span className="step-badge">4</span>
            <div className="step-text">
              <span className="step-title">Acción Humanitaria</span>
              <span className="step-subtitle">
                Damnificados + Desvío Dijkstra
              </span>
            </div>
          </button>
        </div>
      </nav>

      {/* Banner Ejecutivo Animado que aparece cuando estalla una Alerta Roja */}
      <section
        ref={elementRef}
        className="emergency-flash-banner"
        hidden={isHidden}
        data-closing={isClosing ? "" : undefined}
        aria-label="Resumen crítico de Alerta Roja activa"
      >
        <div className="emergency-banner-left">
          <span className="emergency-radar-icon" aria-hidden="true" />
          <div>
            <strong className="emergency-banner-title">
              ALERTA ROJA ACTIVA · PUENTE RÍO MOCHE CERRADO POR DESBORDE
            </strong>
            <p className="emergency-banner-detail">
              Riesgo ML:{" "}
              <strong>{mlPred?.probability_pct.toFixed(1)}%</strong> (
              {mlPred?.predicted_window_label}) · Desvío seguro habilitado por{" "}
              <strong>Carretera PE-10A Laredo</strong> · Damnificados estimados:{" "}
              <strong>
                ~{impact?.total_affected_people.toLocaleString("es-PE")} personas
              </strong>{" "}
              ({impact?.indeci_trucks_required} camiones de ayuda INDECI) ·{" "}
              Heridos/Aislados reportados: <strong>{impact?.estimated_injured_count}</strong>.
            </p>
          </div>
        </div>

        <div className="chip-row">
          <button
            type="button"
            className="btn btn-small btn-danger"
            onClick={onFocusEmergencyMap}
          >
            Enfocar Ruta y Damnificados
          </button>
        </div>
      </section>
    </>
  );
}
