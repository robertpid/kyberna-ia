import React, { useId } from "react";
import MlPredictionCard from "./MlPredictionCard.jsx";
import { useAnimatedNumber } from "../utils/displayTransition.js";

/**
 * Columna izquierda clara y enfocada:
 * 1. Modelo Predictivo ML (Probabilidad %, Ventana de impacto y Reportes de APIs)
 * 2. Credibilidad de Reportes Ciudadanos (Filtro Anti-Fake News NLP)
 */
export default function SurveillanceMetricsPanel({
  decision,
  lastSyncTime,
  animationsPaused,
}) {
  const nlpProgressId = useId();
  const nlp = decision.nlp_validation;

  const animatedCredibility = useAnimatedNumber(
    nlp.credibility_percentage,
    480,
    animationsPaused
  );

  return (
    <section
      className="surveillance-column"
      aria-labelledby="surveillance-panel-heading"
    >
      <div className="block-header">
        <h2 id="surveillance-panel-heading">Predicción y Vigilancia</h2>
        <span className="api-meta">Actualizado: {lastSyncTime}</span>
      </div>

      {/* Tarjeta 1: Modelo Predictivo de Machine Learning y Reportes de APIs */}
      <MlPredictionCard
        decision={decision}
        mlPrediction={decision.ml_prediction}
        animationsPaused={animationsPaused}
      />

      {/* Tarjeta 2: Credibilidad Ciudadana NLP */}
      <article
        className={`metric-card ${
          nlp.is_validated ? "metric-card-critical" : ""
        }`}
      >
        <div className="metric-header">
          <div>
            <span className="eyebrow-tag">VERIFICACIÓN SOCIAL ANTI-FAKE NEWS</span>
            <h3>Credibilidad de Reportes</h3>
          </div>
          <span
            className={nlp.is_validated ? "pill pill-critical" : "pill pill-ok"}
          >
            {nlp.is_validated ? "VALIDADO (> 90%)" : "FILTRANDO RUIDO"}
          </span>
        </div>

        <div className="metric-big-row">
          <p className="metric-big">
            {animatedCredibility.toFixed(1)}
            <span className="metric-unit">%</span>
          </p>
          <span className="api-meta">
            Mínimo requerido: {nlp.validation_threshold_pct.toFixed(0)}%
          </span>
        </div>

        <label htmlFor={nlpProgressId} className="meter-label">
          Consenso entre transportistas, prensa regional y datos oficiales
        </label>
        <progress id={nlpProgressId} max={100} value={nlp.credibility_percentage}>
          {nlp.credibility_percentage.toFixed(1)}%
        </progress>

        <div className="submetrics-grid">
          <div className="mini-stat">
            <span>Reportes Verídicos</span>
            <strong>{nlp.valid_corroborated_reports} confirmados</strong>
          </div>
          <div className="mini-stat">
            <span>Fake News Descartadas</span>
            <strong>{nlp.discarded_fake_reports} bloqueadas</strong>
          </div>
        </div>
      </article>
    </section>
  );
}
