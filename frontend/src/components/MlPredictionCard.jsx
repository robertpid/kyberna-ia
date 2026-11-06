import React from "react";
import { useAnimatedNumber } from "../utils/displayTransition.js";

function getTierMetadata(riskTier) {
  switch (riskTier) {
    case "INMINENTE":
      return {
        badgeLabel: "IMPACTO INMINENTE",
        pillClass: "pill pill-critical",
        strokeColor: "#ff3358",
        cardClass: "ml-card ml-card-imminent",
      };
    case "ALTO":
      return {
        badgeLabel: "RIESGO ALTO",
        pillClass: "pill pill-warn",
        strokeColor: "#ffb020",
        cardClass: "ml-card ml-card-high",
      };
    case "MODERADO":
      return {
        badgeLabel: "VIGILANCIA MODERADA",
        pillClass: "pill pill-warn",
        strokeColor: "#00e5ff",
        cardClass: "ml-card",
      };
    default:
      return {
        badgeLabel: "RIESGO BAJO",
        pillClass: "pill pill-ok",
        strokeColor: "#00f59b",
        cardClass: "ml-card",
      };
  }
}

/**
 * Tarjeta principal de Predicción de Catástrofe con Machine Learning.
 * Muestra el medidor radial animado de probabilidad (%) y cuándo puede ocurrir.
 */
export default function MlPredictionCard({
  decision,
  mlPrediction = decision?.ml_prediction,
  animationsPaused,
}) {
  if (!mlPrediction) {
    return null;
  }

  const animatedProb = useAnimatedNumber(
    mlPrediction.probability_pct,
    560,
    animationsPaused
  );
  const tierMeta = getTierMetadata(mlPrediction.risk_tier);

  const arcLength = 238.76;
  const clampedRatio = Math.max(0, Math.min(1, mlPrediction.probability_pct / 100));
  const strokeDashoffset = arcLength * (1 - clampedRatio);

  const huaico = decision?.huaico_assessment;
  const senamhi = decision?.senamhi_telemetry;
  const rainMm = huaico?.accumulated_rain_mm ?? senamhi?.accumulated_rain_mm ?? 18.5;
  const rainThreshold = huaico?.rain_threshold_mm ?? 50.0;
  const riverM3s = huaico?.river_discharge_m3s ?? senamhi?.river_discharge_m3s ?? 224.0;
  const riverThreshold = huaico?.river_threshold_m3s ?? 280.0;
  const soilSat = huaico?.soil_saturation_pct ?? 42.0;
  const sstAnomaly = mlPrediction?.enso_sst_anomaly_c ?? 0.3;
  const hasSevereEvent = huaico?.has_nearby_severe_event ?? false;

  const isRainExceeded = rainMm >= rainThreshold;
  const isRiverExceeded = riverM3s >= riverThreshold;
  const isSoilSaturated = soilSat >= 80.0;
  const isSstWarm = sstAnomaly >= 1.5;

  const apiReports = [
    {
      source: "SENAMHI · Hidrometeorología",
      tag: isRainExceeded || isRiverExceeded ? "CRÍTICO" : "NORMAL",
      severity: isRainExceeded || isRiverExceeded ? "critical" : "ok",
      reading: `${rainMm.toFixed(1)} mm / ${riverM3s.toFixed(0)} m³/s`,
      why: isRainExceeded || isRiverExceeded
        ? `Lluvia acumulada (${rainMm.toFixed(1)} mm) supera el umbral crítico (${rainThreshold.toFixed(0)} mm) y el caudal del Río Moche (${riverM3s.toFixed(0)} m³/s) excede el nivel de desborde (${riverThreshold.toFixed(0)} m³/s), arrastrando lodo y piedras al puente.`
        : `Lluvia acumulada (${rainMm.toFixed(1)} mm) y caudal (${riverM3s.toFixed(0)} m³/s) en niveles seguros sin peligro de desborde.`,
    },
    {
      source: "Copernicus Sentinel-1 · Radar SAR",
      tag: isSoilSaturated ? "COLMATADO" : "ABSORCIÓN OK",
      severity: isSoilSaturated ? "critical" : "ok",
      reading: `${soilSat.toFixed(1)}% Saturación`,
      why: isSoilSaturated
        ? `Suelo colmatado al ${soilSat.toFixed(1)}% en banda C: pérdida total de capacidad de infiltración, el agua no penetra y discurre como huaico en superficie.`
        : `Suelo con humedad moderada (${soilSat.toFixed(1)}%), capacidad de absorción y drenaje natural activa.`,
    },
    {
      source: "NOAA / ENFEN · SST Niño 1+2",
      tag: isSstWarm ? "ANOMALÍA ALTA" : "NEUTRAL",
      severity: isSstWarm ? "warning" : "ok",
      reading: `+${sstAnomaly.toFixed(1)} °C Térmica`,
      why: isSstWarm
        ? `Calentamiento anómalo en el mar de La Libertad (+${sstAnomaly.toFixed(1)} °C) genera fuerte evaporación oceánica y tormentas convectivas en la cuenca alta.`
        : `Temperatura superficial marina en rango neutral (+${sstAnomaly.toFixed(1)} °C), sin forzamiento convectivo extremo.`,
    },
    {
      source: "NASA EONET v3 · Red Convectiva",
      tag: hasSevereEvent ? "TORMENTA <200km" : "DESPEJADO",
      severity: hasSevereEvent ? "warning" : "ok",
      reading: hasSevereEvent ? "Célula Activa" : "Sin Eventos",
      why: hasSevereEvent
        ? `Célula de tormenta severa activa detectada a menos de 200 km con trayectoria directa hacia el valle de Moche.`
        : `Sin tormentas convectivas severas detectadas en un radio de 200 km del corredor.`,
    },
  ];

  return (
    <article className={tierMeta.cardClass} aria-labelledby="ml-card-heading">
      <div className="metric-header">
        <div>
          <span className="eyebrow-tag">IA PREDICTIVA · MACHINE LEARNING</span>
          <h3 id="ml-card-heading">Probabilidad de Catástrofe</h3>
        </div>
        <span className={tierMeta.pillClass}>{tierMeta.badgeLabel}</span>
      </div>

      {/* Medidor Radial Semicircular Animado */}
      <div className="ml-gauge-wrap">
        <svg
          className="ml-gauge-svg"
          viewBox="0 0 200 112"
          aria-hidden="true"
          focusable="false"
        >
          <path
            className="ml-gauge-track"
            d="M 24 96 A 76 76 0 0 1 176 96"
            fill="none"
            strokeWidth="14"
            strokeLinecap="round"
          />
          <path
            className="ml-gauge-fill"
            d="M 24 96 A 76 76 0 0 1 176 96"
            fill="none"
            stroke={tierMeta.strokeColor}
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={arcLength}
            strokeDashoffset={strokeDashoffset}
          />
        </svg>

        <div className="ml-gauge-readout">
          <strong className="ml-prob-number" style={{ color: tierMeta.strokeColor }}>
            {animatedProb.toFixed(1)}
            <span className="ml-prob-symbol">%</span>
          </strong>
          <span className="ml-prob-caption">Posibilidad de desborde / huaico</span>
        </div>
      </div>

      {/* Ventana Estimada: ¿Cuándo puede ocurrir? */}
      <div className="ml-window-callout">
        <span className="ml-window-label">¿Cuándo puede ocurrir?</span>
        <strong className="ml-window-value">
          {mlPrediction.predicted_window_label}
        </strong>
        <p className="ml-window-action">{mlPrediction.recommended_action}</p>
      </div>

      {/* Reportes Tomados de las APIs: Causa Raíz del Evento */}
      <div className="api-evidence-block">
        <div className="api-evidence-header">
          <span className="meter-label" style={{ margin: 0 }}>
            Reportes de APIs · ¿Por qué ocurrirá el evento?
          </span>
          <span className="pill pill-ok" style={{ fontSize: "0.66rem" }}>
            4 FUENTES EN VIVO
          </span>
        </div>

        <ul className="api-evidence-list" role="list">
          {apiReports.map((item, idx) => (
            <li
              key={idx}
              className={`api-evidence-item api-evidence-item-${item.severity}`}
            >
              <div className="api-evidence-top">
                <span className="api-evidence-source">{item.source}</span>
                <span
                  className={`pill ${
                    item.severity === "critical"
                      ? "pill-critical"
                      : item.severity === "warning"
                      ? "pill-warn"
                      : "pill-ok"
                  }`}
                  style={{ fontSize: "0.62rem" }}
                >
                  {item.tag} · {item.reading}
                </span>
              </div>
              <p className="api-evidence-why">{item.why}</p>
            </li>
          ))}
        </ul>
      </div>

      {/* Variables Principales que Impulsan el Modelo */}
      <div className="ml-drivers-grid">
        {mlPrediction.feature_drivers.slice(0, 4).map((driver) => (
          <div
            key={driver.feature_name}
            className={`mini-stat ${
              driver.is_elevated ? "mini-stat-elevated" : ""
            }`}
          >
            <span>{driver.feature_name}</span>
            <strong>
              {driver.current_value_label} · peso {driver.contribution_pct.toFixed(0)}%
            </strong>
          </div>
        ))}
      </div>
    </article>
  );
}

