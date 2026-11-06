import React, { useId, useRef, useState } from "react";

const QUICK_REPORT_SAMPLES = [
  {
    label: "+ Reporte Real Transportista",
    channel: "WhatsApp Transportistas",
    text: "El río Moche se desbordó y bloqueó la carretera altura puente con lodo y piedras",
  },
  {
    label: "+ Alerta Prensa Regional",
    channel: "Prensa Regional Verificada",
    text: "Urgente en La Libertad: huaico y desborde en Puente Río Moche deja tránsito detenido",
  },
  {
    label: "+ Prueba Cadena Fake News",
    channel: "X (Twitter) Ciudadano",
    text: "URGENTE reenvía esta cadena a 20 contactos, ovni gigante y bonos gratis haz clic aquí!!!",
  },
];

/**
 * Columna derecha clara e intuitiva:
 * 1. Reportes Ciudadanos y Filtro Anti-Fake News
 * 2. Despacho Multicanal (Telegram Real + WhatsApp Mock INDECI)
 * 3. Ficha Técnica Auditada del Modelo Predictivo ML
 */
export default function InteractiveTabsPanel({
  activeTab,
  onChangeTab,
  decision,
  notifications,
  injectedReportsCount,
  isBusy,
  onInjectReport,
  onResetReports,
  onDispatchNotifications,
  onOpenTelegramModal,
  onFocusEmergencyMap,
}) {
  const channelSelectId = useId();
  const reportTextId = useId();
  const reportHintId = useId();
  const tabRefs = useRef([]);

  const [reportFilter, setReportFilter] = useState("all");
  const [channel, setChannel] = useState("WhatsApp Transportistas");
  const [reportText, setReportText] = useState("");
  const [whatsappViewMode, setWhatsappViewMode] = useState("driver");
  const [copiedJson, setCopiedJson] = useState(false);

  const tabs = [
    { id: "nlp", label: "Reportes NLP" },
    { id: "web_scraping", label: "Web Scraping OSINT" },
    { id: "humanitarian", label: "Acción Humanitaria" },
    { id: "notifications", label: "Alertas Enviadas" },
    { id: "ml_audit", label: "Métricas ML" },
  ];

  const handleTabKeyDown = (event, index) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") {
      return;
    }
    event.preventDefault();
    const direction = event.key === "ArrowRight" ? 1 : -1;
    const nextIndex = (index + direction + tabs.length) % tabs.length;
    onChangeTab(tabs[nextIndex].id);
    tabRefs.current[nextIndex]?.focus();
  };

  const allReports = decision.nlp_validation.evaluated_reports || [];
  const filteredReports = allReports.filter((item) => {
    if (reportFilter === "valid") {
      return item.is_corroborated;
    }
    if (reportFilter === "fake") {
      return item.is_fake_or_noise;
    }
    return true;
  });

  const handleReportSubmit = (event) => {
    event.preventDefault();
    if (!reportText.trim()) {
      return;
    }
    onInjectReport(reportText.trim(), channel);
    setReportText("");
  };

  const tgReceipt = notifications?.telegram;
  const waReceipt = notifications?.whatsapp_mock;
  const mlSummary = decision.ml_prediction?.validation_summary;

  const waCleanJson = waReceipt
    ? JSON.stringify(
        {
          provider: waReceipt.provider,
          status: waReceipt.status,
          simulated_message_id: waReceipt.simulated_message_id,
          target_fleet_group: waReceipt.target_fleet_group,
          recipients_notified: waReceipt.recipients_notified,
          route_status_sent: waReceipt.route_status_sent,
          meta_api_cost_avoided_usd: waReceipt.meta_api_cost_avoided_usd,
          dispatched_at_iso: waReceipt.dispatched_at_iso,
        },
        null,
        2
      )
    : "{}";

  const handleCopyJson = async () => {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(waCleanJson);
      setCopiedJson(true);
      setTimeout(() => setCopiedJson(false), 1800);
    }
  };

  return (
    <aside className="controls-column" aria-labelledby="right-panel-heading">
      <div className="block-header">
        <h2 id="right-panel-heading">Operaciones y Reportes</h2>
      </div>

      {/* Barra de Pestañas con soporte de teclado ARIA */}
      <div
        className="tabs-bar"
        role="tablist"
        aria-label="Módulos de reportes, notificaciones y auditoría ML"
      >
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            ref={(el) => {
              tabRefs.current[index] = el;
            }}
            id={`tab-${tab.id}`}
            type="button"
            role="tab"
            className="tab-btn"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            onClick={() => onChangeTab(tab.id)}
            onKeyDown={(e) => handleTabKeyDown(e, index)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* PESTAÑA 1: STREAM CIUDADANO E INYECCIÓN NLP */}
      {activeTab === "nlp" && (
        <div
          id="panel-nlp"
          role="tabpanel"
          aria-labelledby="tab-nlp"
          className="controls-column"
        >
          <form className="panel-block control-form" onSubmit={handleReportSubmit}>
            <div className="block-header" style={{ marginBlockEnd: 0 }}>
              <h3>Simular Reporte Ciudadano</h3>
              {injectedReportsCount > 0 && (
                <button
                  type="button"
                  className="btn btn-chip"
                  onClick={onResetReports}
                >
                  Limpiar ({injectedReportsCount})
                </button>
              )}
            </div>

            <p className="field-hint">
              Prueba con 1 clic un reporte real de carretera o una cadena de{" "}
              <em>fake news</em>:
            </p>
            <div className="chip-row">
              {QUICK_REPORT_SAMPLES.map((sample) => (
                <button
                  key={sample.label}
                  type="button"
                  className="btn btn-chip"
                  disabled={isBusy}
                  onClick={() => onInjectReport(sample.text, sample.channel)}
                >
                  {sample.label}
                </button>
              ))}
            </div>

            <div className="field-group">
              <label htmlFor={channelSelectId}>Fuente informativa</label>
              <select
                id={channelSelectId}
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
              >
                <option value="WhatsApp Transportistas">
                  WhatsApp Transportistas (Peso 0.45)
                </option>
                <option value="Prensa Regional Verificada">
                  Prensa Regional Verificada (Peso 0.65)
                </option>
                <option value="X (Twitter) Ciudadano">
                  Redes Sociales X / Facebook (Peso 0.30)
                </option>
              </select>
            </div>

            <div className="field-group">
              <label htmlFor={reportTextId}>Mensaje recibido</label>
              <p id={reportHintId} className="field-hint">
                El filtro NLP pondera la fuente y bloquea rumores virales.
              </p>
              <textarea
                id={reportTextId}
                rows={2}
                maxLength={280}
                aria-describedby={reportHintId}
                value={reportText}
                onChange={(e) => setReportText(e.target.value)}
                placeholder="Ej. El río Moche se desbordó y bloqueó la carretera..."
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-full"
              disabled={isBusy || !reportText.trim()}
            >
              Validar con Motor NLP
            </button>
          </form>

          <article className="panel-block">
            <div className="block-header">
              <h3>Mensajes Analizados ({filteredReports.length})</h3>
              <div className="chip-row">
                <button
                  type="button"
                  className={`btn btn-chip ${
                    reportFilter === "all" ? "btn-chip-selected" : ""
                  }`}
                  onClick={() => setReportFilter("all")}
                >
                  Todos
                </button>
                <button
                  type="button"
                  className={`btn btn-chip ${
                    reportFilter === "valid" ? "btn-chip-selected" : ""
                  }`}
                  onClick={() => setReportFilter("valid")}
                >
                  Válidos
                </button>
                <button
                  type="button"
                  className={`btn btn-chip ${
                    reportFilter === "fake" ? "btn-chip-selected" : ""
                  }`}
                  onClick={() => setReportFilter("fake")}
                >
                  Fake News
                </button>
              </div>
            </div>

            <ul className="reports-feed" role="list">
              {filteredReports.map((rep) => (
                <li
                  key={rep.report_id}
                  className={`report-card ${
                    rep.is_fake_or_noise ? "report-card-fake" : ""
                  }`}
                >
                  <div className="report-top">
                    <span>
                      {rep.source_channel} · {rep.author_handle}
                    </span>
                    <span>hace {rep.minutes_ago} min</span>
                  </div>
                  <p className="report-quote">“{rep.raw_text}”</p>
                  <div className="report-tag">
                    {rep.is_fake_or_noise
                      ? "BLOQUEADO · FAKE NEWS / CADENA VIRAL"
                      : rep.is_corroborated
                      ? `CONFIRMADO · ${rep.detected_incident} (peso ${Math.round(
                          rep.source_base_weight * 100
                        )}%)`
                      : `EN OBSERVACIÓN · ${rep.detected_incident}`}
                  </div>
                </li>
              ))}
            </ul>
          </article>
        </div>
      )}

      {/* PESTAÑA 2: NOTIFICACIONES (TELEGRAM REAL + WHATSAPP MOCK INDECI) */}
      {activeTab === "notifications" && (
        <div
          id="panel-notifications"
          role="tabpanel"
          aria-labelledby="tab-notifications"
          className="controls-column"
        >
          <article className="panel-block">
            <div className="block-header">
              <div>
                <span className="eyebrow-tag">CANAL OFICIAL TELEGRAM</span>
                <h3>Telegram Bot API (Envío Real)</h3>
              </div>
              <span
                className={
                  tgReceipt?.delivered_live ? "pill pill-ok" : "pill pill-warn"
                }
              >
                {tgReceipt?.delivered_live ? "ENVIADO EN VIVO" : "LISTO"}
              </span>
            </div>

            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBlock: "0.4rem" }}>
              <span className="api-meta" style={{ margin: 0 }}>Tono de Comunicación:</span>
              <span className={`pill ${decision.notification_tone === "OPERATIVO_CRITICO" ? "pill-critical" : "pill-ok"}`}>
                {decision.notification_tone === "INFORMATIVO_NO_ALARMISTA"
                  ? "INFORMATIVO (NO ALARMISTA)"
                  : decision.notification_tone}
              </span>
            </div>
            <p className="field-hint" style={{ marginBlockEnd: "0.55rem" }}>
              {decision.notification_tone === "INFORMATIVO_NO_ALARMISTA"
                ? "En Etapas 1 y 2 el mensaje informa con calma y recomienda precaución vial sin desatar pánico ciudadano."
                : "En Etapas 3 y 4 se emite la orden logística de desvío e instrucciones operacionales a convoyes de INDECI."}
            </p>
            {tgReceipt?.telegram_message_id && (
              <p className="api-meta" style={{ marginBlockEnd: "0.55rem" }}>
                Entregado · Chat: {tgReceipt.target_chat_masked} · ID:{" "}
                {tgReceipt.telegram_message_id}
              </p>
            )}
            <div className="button-row">
              <button
                type="button"
                className="btn btn-primary"
                disabled={isBusy}
                onClick={onDispatchNotifications}
              >
                Despachar Alerta Ahora
              </button>
              <button
                type="button"
                className="btn btn-accent"
                onClick={onOpenTelegramModal}
              >
                Vincular Bot
              </button>
            </div>
          </article>

          <article className="panel-block">
            <div className="block-header">
              <h3>WhatsApp Flota INDECI (Mock)</h3>
              <span className="pill pill-ok">$0 COSTO META</span>
            </div>

            <div className="chip-row" style={{ marginBlockEnd: "0.55rem" }}>
              <button
                type="button"
                className={`btn btn-chip ${
                  whatsappViewMode === "driver" ? "btn-chip-selected" : ""
                }`}
                onClick={() => setWhatsappViewMode("driver")}
              >
                Mensaje al Transportista
              </button>
              <button
                type="button"
                className={`btn btn-chip ${
                  whatsappViewMode === "json" ? "btn-chip-selected" : ""
                }`}
                onClick={() => setWhatsappViewMode("json")}
              >
                Recibo JSON
              </button>
              {whatsappViewMode === "json" && (
                <button
                  type="button"
                  className="btn btn-chip"
                  onClick={handleCopyJson}
                >
                  {copiedJson ? "¡Copiado!" : "Copiar JSON"}
                </button>
              )}
            </div>

            {whatsappViewMode === "driver" ? (
              <div className="whatsapp-preview-bubble">
                {waReceipt?.formatted_console_body ||
                  "Sin boletín emitido aún."}
              </div>
            ) : (
              <figure className="code-figure">
                <figcaption>
                  Comprobante JSON simulado sin costos de la API de Meta:
                </figcaption>
                <pre tabIndex={0}>
                  <code>{waCleanJson}</code>
                </pre>
              </figure>
            )}
          </article>
        </div>
      )}

      {/* PESTAÑA: WEB SCRAPING EN VIVO (NOTICIAS Y REDES EN TIEMPO REAL) */}
      {activeTab === "web_scraping" && (
        <div
          id="panel-web_scraping"
          role="tabpanel"
          aria-labelledby="tab-web_scraping"
          className="controls-column"
        >
          <article className="panel-block">
            <div className="block-header">
              <div>
                <span className="eyebrow-tag">
                  {decision.current_stage?.includes("ETAPA 4")
                    ? "ETAPA 4 · INTELIGENCIA DE FUENTES (INTEGRADA A EDAN)"
                    : "ETAPA 3 · INTELIGENCIA DE FUENTES ABIERTAS"}
                </span>
                <h3>Web Scraping de Noticias y Redes</h3>
              </div>
              <span
                className={`pill ${
                  decision.web_scraping_audit?.is_scraping_active
                    ? "pill-critical"
                    : "pill-ok"
                }`}
              >
                {decision.web_scraping_audit?.is_scraping_active
                  ? "ESCANEANDO EN VIVO"
                  : "EN ESPERA (≤4h)"}
              </span>
            </div>

            <p className="field-hint" style={{ marginBlockEnd: "0.6rem" }}>
              {decision.web_scraping_audit?.summary_headline ||
                "Se activa automáticamente cuando el Modelo ML proyecta lluvias intensas en <= 4 horas."}
            </p>

            <div className="submetrics-grid">
              <div className="mini-stat">
                <span>Portales Escaneados</span>
                <strong>
                  {decision.web_scraping_audit?.total_sources_scanned || 0}
                </strong>
              </div>
              <div className="mini-stat">
                <span>Calles Inundadas</span>
                <strong style={{ color: "#ff6b8b" }}>
                  {decision.web_scraping_audit?.flooded_streets_count || 0}
                </strong>
              </div>
              <div className="mini-stat">
                <span>Casas en Riesgo</span>
                <strong style={{ color: "#ffb86c" }}>
                  {decision.web_scraping_audit?.structures_at_risk_count || 0}
                </strong>
              </div>
              <div className="mini-stat">
                <span>Heridos / Aislados</span>
                <strong style={{ color: "#ff3358" }}>
                  {decision.web_scraping_audit?.isolated_injured_signals_count || 0}
                </strong>
              </div>
            </div>

            <div className="block-header" style={{ marginBlockStart: "0.85rem", marginBlockEnd: "0.4rem" }}>
              <h4 style={{ margin: 0, fontSize: "0.85rem", color: "#6df" }}>
                Hallazgos Extraídos (RPP, La Industria, Correo, X/Twitter)
              </h4>
            </div>

            <ul className="reports-list" role="list">
              {(decision.web_scraping_audit?.items || []).map((item, idx) => (
                <li key={idx} className="report-item" style={{ borderLeftColor: "#ff6b8b" }}>
                  <div className="report-item-top">
                    <span className="report-channel">{item.source_name}</span>
                    <span className="pill pill-danger" style={{ fontSize: "0.68rem" }}>
                      {item.category_label || item.category}
                    </span>
                    <span className="report-time">{item.timestamp_label}</span>
                  </div>
                  <strong style={{ display: "block", fontSize: "0.82rem", marginBlock: "0.25rem", color: "#f0f4f8" }}>
                    {item.headline}
                  </strong>
                  <p className="report-body" style={{ fontSize: "0.78rem", color: "#c0c8d8" }}>
                    {item.snippet_text}
                  </p>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem", color: "#8fa0b5", marginBlockStart: "0.3rem" }}>
                    <span>📍 {item.detected_location}</span>
                    <span>Severidad: {item.severity_level}</span>
                  </div>
                </li>
              ))}
            </ul>
          </article>
        </div>
      )}

      {/* PESTAÑA: ACCIÓN HUMANITARIA (ETAPA 4 · DAMNIFICADOS, KITS SPHERE Y DESVÍO DIJKSTRA) */}
      {activeTab === "humanitarian" && (
        <div
          id="panel-humanitarian"
          role="tabpanel"
          aria-labelledby="tab-humanitarian"
          className="controls-column"
        >
          <article className="panel-block">
            <div className="block-header">
              <div>
                <span className="eyebrow-tag">ETAPA 4 · ACCIÓN HUMANITARIA Y DESVÍO DIJKSTRA</span>
                <h3>Cálculo de Damnificados y Despacho Logístico INDECI</h3>
              </div>
              <span
                className={`pill ${
                  decision.current_system_state === "ALERTA ROJA"
                    ? "pill-critical"
                    : "pill-ok"
                }`}
              >
                {decision.current_system_state === "ALERTA ROJA"
                  ? "DESVÍO VIAL ACTIVO"
                  : "CORREDOR LIBRE"}
              </span>
            </div>

            <p className="field-hint" style={{ marginBlockEnd: "0.6rem" }}>
              Cálculo automatizado de necesidades humanitarias bajo estándar internacional SPHERE y re-enrutamiento logístico dinámico ante colapso en el Puente Río Moche.
            </p>

            <div className="submetrics-grid">
              <div className="mini-stat">
                <span>Población Afectada</span>
                <strong style={{ color: "#ff6b8b" }}>
                  ~{decision.humanitarian_impact?.total_affected_people ? decision.humanitarian_impact.total_affected_people.toLocaleString("es-PE") : 0} hab
                </strong>
                <small style={{ color: "#8fa0b5" }}>
                  ({decision.humanitarian_impact?.total_affected_families || 0} familias)
                </small>
              </div>
              <div className="mini-stat">
                <span>Convoy INDECI Asignado</span>
                <strong style={{ color: "#54d7f7" }}>
                  {decision.humanitarian_impact?.indeci_trucks_required || 0} Camiones
                </strong>
                <small style={{ color: "#8fa0b5" }}>
                  ({decision.humanitarian_impact?.total_cargo_tons || 0} TM de carga)
                </small>
              </div>
              <div className="mini-stat">
                <span>Kits de Alimentos (18kg)</span>
                <strong style={{ color: "#ffb86c" }}>
                  {decision.humanitarian_impact?.food_kits_18kg_count || 0} kits
                </strong>
                <small style={{ color: "#8fa0b5" }}>1 por familia / 7 días</small>
              </div>
              <div className="mini-stat">
                <span>Agua Potable Total</span>
                <strong style={{ color: "#50fa7b" }}>
                  {decision.humanitarian_impact?.water_liters_total ? decision.humanitarian_impact.water_liters_total.toLocaleString("es-PE") : 0} L
                </strong>
                <small style={{ color: "#8fa0b5" }}>15 L/hab/día (SPHERE)</small>
              </div>
              <div className="mini-stat">
                <span>Carpas Humanitarias</span>
                <strong style={{ color: "#bd93f9" }}>
                  {decision.humanitarian_impact?.tents_required || 0} carpas
                </strong>
                <small style={{ color: "#8fa0b5" }}>Para 60% casas colapsadas</small>
              </div>
              <div className="mini-stat">
                <span>Frazadas Térmicas</span>
                <strong style={{ color: "#f1fa8c" }}>
                  {decision.humanitarian_impact?.blankets_required ? decision.humanitarian_impact.blankets_required.toLocaleString("es-PE") : 0} un.
                </strong>
                <small style={{ color: "#8fa0b5" }}>1 por persona afectada</small>
              </div>
            </div>

            <div className="block-header" style={{ marginBlockStart: "0.85rem", marginBlockEnd: "0.4rem" }}>
              <h4 style={{ margin: 0, fontSize: "0.85rem", color: "#6df" }}>
                Plan Logístico de Desvío Vial (Dijkstra / OSRM)
              </h4>
            </div>

            <ul className="trace-list" role="list">
              <li className="trace-item" style={{ borderLeftColor: "#ff3358" }}>
                <strong>Vía Crítica Bloqueada (Inundada):</strong>
                Puente Río Moche - Panamericana Tradicional Sur (Caudal crítico &gt; 350 m³/s). Tránsito pesado cerrado.
              </li>
              <li className="trace-item" style={{ borderLeftColor: "#50fa7b" }}>
                <strong>Corredor de Desvío Seguro Habilitado:</strong>
                {decision.safe_route?.route_name || "Carretera Industrial PE-10A Laredo · Cota Alta Conache · Alto Salaverry"}
              </li>
              <li className="trace-item">
                <strong>Métricas Operativas del Desvío:</strong>
                Distancia total: <strong>{decision.safe_route?.total_distance_km ? decision.safe_route.total_distance_km.toFixed(1) : "71.0"} km</strong> · Tiempo estimado: <strong>{decision.safe_route?.estimated_travel_minutes || 69} min</strong> (Tránsito fluido asegurado).
              </li>
            </ul>

            <div className="button-row" style={{ marginBlockStart: "0.75rem" }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={isBusy}
                onClick={onDispatchNotifications}
              >
                Reenviar Alerta a Flota INDECI (Telegram)
              </button>
              {onFocusEmergencyMap && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={onFocusEmergencyMap}
                >
                  Enfocar Ruta en Mapa
                </button>
              )}
            </div>
          </article>
        </div>
      )}

      {/* PESTAÑA 3: FICHA TÉCNICA Y MÉTRICAS DEL MODELO PREDICTIVO ML */}
      {activeTab === "ml_audit" && mlSummary && (
        <div
          id="panel-ml_audit"
          role="tabpanel"
          aria-labelledby="tab-ml_audit"
          className="controls-column"
        >
          <article className="panel-block">
            <div className="block-header">
              <h3>Validación del Modelo Predictivo</h3>
              <span className="pill pill-ok">AUDITADO</span>
            </div>
            <p className="field-hint" style={{ marginBlockEnd: "0.65rem" }}>
              Entrenado con partición estrictamente cronológica sobre series
              históricas del Fenómeno del Niño (1998–2026) sin fuga de datos.
            </p>

            <div className="submetrics-grid">
              <div className="mini-stat">
                <span>ROC-AUC (Modelo Activo)</span>
                <strong>{mlSummary.selected_roc_auc.toFixed(3)}</strong>
              </div>
              <div className="mini-stat">
                <span>ROC-AUC (Base Lineal)</span>
                <strong>{mlSummary.baseline_roc_auc.toFixed(3)}</strong>
              </div>
              <div className="mini-stat">
                <span>F1-Score en Test</span>
                <strong>{mlSummary.selected_f1_score.toFixed(3)}</strong>
              </div>
              <div className="mini-stat">
                <span>Error Ventana (MAE)</span>
                <strong>±{mlSummary.time_regressor_mae_hours} h</strong>
              </div>
            </div>

            <ul className="trace-list" role="list" style={{ marginBlockStart: "0.7rem" }}>
              <li className="trace-item">
                <strong>Modelo Seleccionado en Producción</strong>
                {mlSummary.selected_model_name} (superó a{" "}
                {mlSummary.baseline_model_name} en validación cronológica).
              </li>
              <li className="trace-item">
                <strong>Partición Temporal Sin Fuga (Data Leakage = 0)</strong>
                Entrenamiento: {mlSummary.train_samples} ventanas · Validación:{" "}
                {mlSummary.validation_samples} · Test ciego:{" "}
                {mlSummary.test_samples} ({mlSummary.missing_values_imputed}{" "}
                valores nulos imputados con mediana de Train).
              </li>
              <li className="trace-item">
                <strong>Variables Hidrometeorológicas Evaluadas</strong>
                Lluvia acumulada 7d (mm), caudal Río Moche (m³/s), saturación SAR
                Sentinel-1 (%), intensidad horaria (mm/h), anomalía térmica Niño
                1+2 (+{decision.ml_prediction.enso_sst_anomaly_c}°C) y densidad NLP.
              </li>
            </ul>
          </article>
        </div>
      )}
    </aside>
  );
}
