import React, { useEffect, useId, useRef, useState } from "react";

/**
 * Modal nativo <dialog> controlado con useRef().showModal() para configurar
 * opcionalmente el Bot gratuito de Telegram y probar envíos reales en vivo.
 */
export default function TelegramConfigDialog({
  isOpen,
  initialToken,
  initialChatId,
  onClose,
  onSaveAndSend,
}) {
  const dialogRef = useRef(null);
  const titleId = useId();
  const tokenInputId = useId();
  const tokenHintId = useId();
  const chatInputId = useId();
  const chatHintId = useId();

  const [botToken, setBotToken] = useState(initialToken);
  const [chatId, setChatId] = useState(initialChatId);

  useEffect(() => {
    const dialogNode = dialogRef.current;
    if (!dialogNode) {
      return;
    }
    if (isOpen && !dialogNode.open) {
      dialogNode.showModal();
    } else if (!isOpen && dialogNode.open) {
      dialogNode.close();
    }
  }, [isOpen]);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSaveAndSend(botToken.trim(), chatId.trim());
  };

  return (
    <dialog
      ref={dialogRef}
      closedby="any"
      aria-labelledby={titleId}
      onClose={onClose}
    >
      <div className="dialog-surface">
        <div className="dialog-header">
          <h2 id={titleId}>Configurar Envío Real · Telegram Bot API</h2>
          <button type="button" className="btn btn-small" onClick={onClose}>
            Cerrar
          </button>
        </div>

        <p className="dialog-intro">
          Kyberna IA envía alertas reales gratuitas mediante{" "}
          <code>api.telegram.org</code>. Puedes definir las variables en tu
          archivo local <code>.env</code> o ingresarlas aquí para disparar una
          prueba en vivo a tu teléfono:
        </p>

        <ol className="setup-steps">
          <li>
            En Telegram, escribe a <strong>@BotFather</strong> el comando{" "}
            <code>/newbot</code> y copia el Token HTTP.
          </li>
          <li>
            Envía un mensaje a tu bot y consulta tu Chat ID numérico en{" "}
            <strong>@userinfobot</strong>.
          </li>
        </ol>

        <form className="control-form" onSubmit={handleSubmit}>
          <div className="field-group">
            <label htmlFor={tokenInputId}>
              Telegram Bot Token (entrada protegida)
            </label>
            <p id={tokenHintId} className="field-hint">
              Nunca se imprime en logs ni se expone fuera de tu servidor local.
            </p>
            <input
              id={tokenInputId}
              type="password"
              autoComplete="new-password"
              aria-describedby={tokenHintId}
              value={botToken}
              onChange={(e) => setBotToken(e.target.value)}
              placeholder="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
            />
          </div>

          <div className="field-group">
            <label htmlFor={chatInputId}>Telegram Chat ID</label>
            <p id={chatHintId} className="field-hint">
              ID personal o de grupo de transportistas (ej.{" "}
              <code>987654321</code> o <code>-100123456789</code>).
            </p>
            <input
              id={chatInputId}
              type="text"
              inputMode="numeric"
              aria-describedby={chatHintId}
              value={chatId}
              onChange={(e) => setChatId(e.target.value)}
              placeholder="Ej. 987654321"
            />
          </div>

          <div className="button-row">
            <button type="submit" className="btn btn-primary btn-full">
              Vincular en Sesión y Enviar Alerta Real Ahora
            </button>
          </div>
        </form>
      </div>
    </dialog>
  );
}

