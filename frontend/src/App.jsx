import React, { useCallback, useEffect, useRef, useState } from "react";
import TopCommandBar from "./components/TopCommandBar.jsx";
import SurveillanceMetricsPanel from "./components/SurveillanceMetricsPanel.jsx";
import InteractivePeruMap from "./components/InteractivePeruMap.jsx";
import InteractiveTabsPanel from "./components/InteractiveTabsPanel.jsx";
import TelegramConfigDialog from "./components/TelegramConfigDialog.jsx";

/**
 * Aplicación raíz en React de Kyberna IA.
 * Conecta el Modelo Predictivo ML, el Panel de Vigilancia, el Mapa de Carreteras OSRM
 * y las alertas multicanal con transiciones accesibles de alta precisión.
 */
export default function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [isBusy, setIsBusy] = useState(false);
  const [errorBanner, setErrorBanner] = useState("");
  const [lastSyncTime, setLastSyncTime] = useState("--:--:--");
  const [autoPolling, setAutoPolling] = useState(false);
  const [animationsPaused, setAnimationsPaused] = useState(false);
  const [activeRightTab, setActiveRightTab] = useState("nlp");
  const [focusTriggerCount, setFocusTriggerCount] = useState(0);
  const [alertFlashPulse, setAlertFlashPulse] = useState(false);
  const [isTelegramModalOpen, setIsTelegramModalOpen] = useState(false);
  const [telegramCreds, setTelegramCreds] = useState({
    botToken: "",
    chatId: "",
  });

  const [politeAnnouncement, setPoliteAnnouncement] = useState("");
  const [assertiveAnnouncement, setAssertiveAnnouncement] = useState("");
  const previousStateRef = useRef(null);

  const applyServerSnapshot = useCallback(
    (payload) => {
      setDashboardData(payload);
      setLastSyncTime(new Date().toLocaleTimeString("es-PE"));
      setErrorBanner("");

      const nextState = payload?.decision?.current_system_state;
      if (nextState) {
        document.title = `${nextState} | Kyberna IA`;
        if (previousStateRef.current !== nextState) {
          if (nextState === "ALERTA ROJA") {
            if (previousStateRef.current !== null && !animationsPaused) {
              setAlertFlashPulse(true);
              window.setTimeout(() => setAlertFlashPulse(false), 1100);
            }
            if (!isTelegramModalOpen) {
              setAssertiveAnnouncement(
                `Alerta Roja activada. Probabilidad de catástrofe ${payload?.decision?.ml_prediction?.probability_pct?.toFixed(
                  1
                )} por ciento. Nueva ruta segura habilitada.`
              );
            }
          } else if (!isTelegramModalOpen) {
            setPoliteAnnouncement(
              "Modo Vigilancia activo. Corredor Panamericana Norte despejado."
            );
          }
          previousStateRef.current = nextState;
        }
      }
    },
    [animationsPaused, isTelegramModalOpen]
  );

  const fetchSurveillanceSnapshot = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/surveillance");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const json = await response.json();
      applyServerSnapshot(json);
    } catch (err) {
      setErrorBanner(
        `No se pudo conectar con el Backend FastAPI (${err.message}).`
      );
    }
  }, [applyServerSnapshot]);

  useEffect(() => {
    fetchSurveillanceSnapshot();
  }, [fetchSurveillanceSnapshot]);

  useEffect(() => {
    if (!autoPolling) {
      return undefined;
    }
    const timerId = window.setInterval(() => {
      fetchSurveillanceSnapshot();
    }, 5000);
    return () => window.clearInterval(timerId);
  }, [autoPolling, fetchSurveillanceSnapshot]);

  const executeSimulation = async (options) => {
    setIsBusy(true);
    try {
      const response = await fetch("/api/v1/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...options,
          telegram_bot_token: telegramCreds.botToken || null,
          telegram_chat_id: telegramCreds.chatId || null,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const json = await response.json();
      applyServerSnapshot(json);
    } catch (err) {
      setErrorBanner(`Error ejecutando simulación: ${err.message}`);
    } finally {
      setIsBusy(false);
    }
  };

  const handleSetScenario = (scenarioName, rainMm) => {
    executeSimulation({
      scenario: scenarioName,
      custom_rain_mm: rainMm,
      dispatch_notifications: true,
    });
  };

  const handleSelectStage = async (stageId) => {
    setIsBusy(true);
    try {
      const res = await fetch("/api/v1/stage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stage: stageId,
          dispatch_notifications: true,
          telegram_bot_token: telegramCreds.botToken || null,
          telegram_chat_id: telegramCreds.chatId || null,
        }),
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const json = await res.json();
      applyServerSnapshot(json);
      if (stageId === "etapa_3") {
        setActiveRightTab("web_scraping");
      } else if (stageId === "etapa_2") {
        setActiveRightTab("notifications");
      }
    } catch (err) {
      setErrorBanner(`Error activando etapa: ${err.message}`);
    } finally {
      setIsBusy(false);
    }
  };

  const handleTestFakeNewsScenario = () => {
    setActiveRightTab("nlp");
    executeSimulation({
      scenario: "vigilancia",
      custom_rain_mm: 24.0,
      new_citizen_report_text:
        "URGENTE reenvía esta cadena a 20 contactos, ovni gigante y bonos gratis haz clic aquí!!!",
      new_report_channel: "X (Twitter) Bot",
      dispatch_notifications: true,
    });
  };

  const handleApplyCustomRain = (rainMm) => {
    const scenarioName = rainMm > 50.0 ? "emergencia" : "vigilancia";
    executeSimulation({
      scenario: scenarioName,
      custom_rain_mm: rainMm,
      dispatch_notifications: true,
    });
  };

  const handleInjectReport = (text, channel) => {
    const currentRain =
      dashboardData?.decision?.huaico_assessment?.accumulated_rain_mm ?? 58.4;
    const currentScenario = dashboardData?.active_scenario || "emergencia";
    executeSimulation({
      scenario: currentScenario,
      custom_rain_mm: currentRain,
      new_citizen_report_text: text,
      new_report_channel: channel,
      dispatch_notifications: true,
    });
  };

  const handleResetReports = async () => {
    setIsBusy(true);
    try {
      const res = await fetch("/api/v1/reset-reports", { method: "POST" });
      if (res.ok) {
        const json = await res.json();
        applyServerSnapshot(json);
      }
    } finally {
      setIsBusy(false);
    }
  };

  const handleDispatchNotifications = async (
    overrideToken = telegramCreds.botToken,
    overrideChat = telegramCreds.chatId
  ) => {
    setIsBusy(true);
    try {
      const res = await fetch("/api/v1/notify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          telegram_bot_token: overrideToken || null,
          telegram_chat_id: overrideChat || null,
        }),
      });
      if (res.ok) {
        const json = await res.json();
        applyServerSnapshot(json);
        setActiveRightTab("notifications");
      }
    } finally {
      setIsBusy(false);
    }
  };

  const handleSaveTelegramAndSend = (token, chat) => {
    setTelegramCreds({ botToken: token, chatId: chat });
    setIsTelegramModalOpen(false);
    handleDispatchNotifications(token, chat);
  };

  if (!dashboardData) {
    return (
      <div className="dashboard-shell" style={{ placeItems: "center" }}>
        <p role="status">Cargando Centro de Mando y Modelo ML de Kyberna IA...</p>
      </div>
    );
  }

  return (
    <div
      className={`dashboard-shell ${
        alertFlashPulse ? "dashboard-alert-triggered" : ""
      } ${animationsPaused ? "motion-paused" : ""}`}
    >
      <a href="#main-heading" className="skip-link visually-hidden">
        Saltar al panel principal
      </a>

      {/* Regiones centralizadas de anuncios para lectores de pantalla */}
      <div className="visually-hidden" aria-live="polite" aria-atomic="true">
        {politeAnnouncement}
      </div>
      <div className="visually-hidden" aria-live="assertive" aria-atomic="true">
        {assertiveAnnouncement}
      </div>

      <TopCommandBar
        decision={dashboardData.decision}
        isBusy={isBusy}
        autoPolling={autoPolling}
        animationsPaused={animationsPaused}
        onSetScenario={handleSetScenario}
        onSelectStage={handleSelectStage}
        onTestFakeNewsScenario={handleTestFakeNewsScenario}
        onTogglePolling={() => setAutoPolling((prev) => !prev)}
        onToggleAnimations={() => setAnimationsPaused((prev) => !prev)}
        onOpenTelegramModal={() => setIsTelegramModalOpen(true)}
        onFocusEmergencyMap={() => setFocusTriggerCount((c) => c + 1)}
      />

      {errorBanner && (
        <div
          role="alert"
          style={{
            padding: "0.55rem 1.25rem",
            backgroundColor: "#3a0b17",
            color: "#ffb3c1",
            fontSize: "0.82rem",
          }}
        >
          {errorBanner}
        </div>
      )}

      <main className="workspace-grid">
        <SurveillanceMetricsPanel
          decision={dashboardData.decision}
          lastSyncTime={lastSyncTime}
          animationsPaused={animationsPaused}
        />

        <InteractivePeruMap
          decision={dashboardData.decision}
          focusTriggerCount={focusTriggerCount}
          animationsPaused={animationsPaused}
        />

        <InteractiveTabsPanel
          activeTab={activeRightTab}
          onChangeTab={setActiveRightTab}
          decision={dashboardData.decision}
          notifications={dashboardData.notifications}
          injectedReportsCount={dashboardData.injected_reports_count}
          isBusy={isBusy}
          onInjectReport={handleInjectReport}
          onResetReports={handleResetReports}
          onDispatchNotifications={() => handleDispatchNotifications()}
          onOpenTelegramModal={() => setIsTelegramModalOpen(true)}
        />
      </main>

      <footer className="footer-bar">
        <span>
          Kyberna IA · Orquestador Predictivo ML + Rutas Viales OSRM (La Libertad, Perú)
        </span>
        <span>
          Incidente: {dashboardData.decision.incident_code} · Modelo:{" "}
          {dashboardData.decision.ml_prediction?.validation_summary
            ?.selected_model_name || "ML Activo"}
        </span>
      </footer>

      <TelegramConfigDialog
        isOpen={isTelegramModalOpen}
        initialToken={telegramCreds.botToken}
        initialChatId={telegramCreds.chatId}
        onClose={() => setIsTelegramModalOpen(false)}
        onSaveAndSend={handleSaveTelegramAndSend}
      />
    </div>
  );
}
