"""Motor Predictivo de Machine Learning para Catástrofes Hidrometeorológicas.

Implementa un flujo riguroso de Ciencia de Datos y ML supervisado en la Capa de
Negocio siguiendo mejores prácticas de ingeniería:
1. Partición estrictamente cronológica (70% Train / 15% Validation / 15% Test)
   ANTES de ajustar cualquier imputador o estandarizador (cero fuga de datos).
2. Auditoría e imputación de valores faltantes (mediana del conjunto de entrenamiento)
   más indicador de imputación y estandarización Z-Score ajustada solo en Train.
3. Entrenamiento y comparación de dos modelos clasificadores supervisados:
   - Modelo Base: Regresión Logística Regularizada L2 (optimización L-BFGS-B).
   - Modelo Avanzado: Clasificador No-Lineal RBF con Características Aleatorias de
     Fourier (Random Kitchen Sinks + L2) que captura interacciones suelo-lluvia-caudal.
4. Regresor supervisado no-lineal Ridge-RBF para estimar en cuántas horas podría
   ocurrir el impacto catastrófico y proyectar el riesgo a +3h, +6h, +12h y +24h.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize
from scipy.special import expit

from data.historical_fen_dataset import (
    FEATURE_COLUMN_NAMES,
    load_historical_moche_fen_dataset,
)
from models.schemas import (
    HorizonForecastPoint,
    KybernaDomainError,
    MlCatastrophePrediction,
    MlFeatureDriver,
    MlModelValidationSummary,
    NasaEonetEvent,
    NlpValidationResult,
    SenamhiTelemetry,
    SentinelRadarReading,
)
from utils.logger_config import get_tier_logger

ML_LOGGER = get_tier_logger("kyberna.logic.ml_catastrophe_predictor")

HUMAN_FEATURE_LABELS: Final[tuple[str, ...]] = (
    "Lluvia Acumulada SENAMHI",
    "Caudal Río Moche",
    "Saturación Suelo SAR",
    "Intensidad Lluvia Horaria",
    "Anomalía Térmica El Niño",
    "Densidad Reportes NLP",
)


class MlPipelineTrainingError(KybernaDomainError):
    """Excepción controlada para errores de entrenamiento o inferencia ML."""


@dataclass(frozen=True)
class FittedPreprocessor:
    """Parámetros de imputación y escalado ajustados exclusivamente en Train."""

    train_medians: NDArray[np.float64]
    train_means: NDArray[np.float64]
    train_stds: NDArray[np.float64]
    total_missing_imputed: int


@dataclass(frozen=True)
class BinaryClassificationMetrics:
    """Métricas de evaluación sobre partición de validación o prueba."""

    roc_auc: float
    f1_score: float
    precision: float
    recall: float
    accuracy: float


@dataclass(frozen=True)
class TrainedCatastropheArtifacts:
    """Artefactos entrenados y validados listos para inferencia en tiempo real."""

    preprocessor: FittedPreprocessor
    use_nonlinear_rff: bool
    selected_weights: NDArray[np.float64]
    selected_bias: float
    linear_explain_weights: NDArray[np.float64]
    rff_omega: NDArray[np.float64]
    rff_phase: NDArray[np.float64]
    time_reg_weights: NDArray[np.float64]
    time_reg_bias: float
    validation_summary: MlModelValidationSummary


def fit_train_only_preprocessor(
    raw_train_features: NDArray[np.float64],
    total_dataset_missing: int,
) -> FittedPreprocessor:
    """Ajusta medianas de imputación y Z-score usando únicamente datos de entrenamiento."""
    train_medians = np.nanmedian(raw_train_features, axis=0)
    imputed_train = np.where(
        np.isnan(raw_train_features),
        train_medians,
        raw_train_features,
    )
    train_means = np.mean(imputed_train, axis=0)
    train_stds = np.where(
        np.std(imputed_train, axis=0) < 1e-6,
        1.0,
        np.std(imputed_train, axis=0),
    )
    return FittedPreprocessor(
        train_medians=train_medians,
        train_means=train_means,
        train_stds=train_stds,
        total_missing_imputed=total_dataset_missing,
    )


def transform_features_matrix(
    raw_features: NDArray[np.float64],
    preprocessor: FittedPreprocessor,
) -> NDArray[np.float64]:
    """Imputa nulos y estandariza una matriz de entrada sin fuga de información."""
    imputed_matrix = np.where(
        np.isnan(raw_features),
        preprocessor.train_medians,
        raw_features,
    )
    return (imputed_matrix - preprocessor.train_means) / preprocessor.train_stds


def project_random_fourier_features(
    scaled_features: NDArray[np.float64],
    rff_omega: NDArray[np.float64],
    rff_phase: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Proyecta variables hidrológicas hacia un espacio kernel RBF + lineal concatenado."""
    projection = np.sqrt(2.0 / rff_omega.shape[1]) * np.cos(
        scaled_features @ rff_omega + rff_phase
    )
    return np.hstack((scaled_features, projection))


def fit_l2_logistic_classifier(
    design_matrix: NDArray[np.float64],
    binary_targets: NDArray[np.int64],
    l2_penalty: float = 0.85,
) -> tuple[NDArray[np.float64], float]:
    """Entrena un clasificador logístico regularizado L2 mediante L-BFGS-B vectorizado."""
    sample_count, feature_dim = design_matrix.shape
    targets_float = binary_targets.astype(np.float64)
    initial_params = np.zeros(feature_dim + 1, dtype=np.float64)

    def objective_and_gradient(
        params: NDArray[np.float64],
    ) -> tuple[float, NDArray[np.float64]]:
        weights = params[:-1]
        bias = float(params[-1])
        logits = design_matrix @ weights + bias
        probabilities = expit(logits)
        clipped_probs = np.clip(probabilities, 1e-9, 1.0 - 1e-9)

        neg_log_likelihood = -float(
            np.mean(
                targets_float * np.log(clipped_probs)
                + (1.0 - targets_float) * np.log(1.0 - clipped_probs)
            )
        )
        reg_term = 0.5 * (l2_penalty / sample_count) * float(np.sum(weights**2))

        error_vector = (probabilities - targets_float) / sample_count
        grad_weights = (design_matrix.T @ error_vector) + (
            (l2_penalty / sample_count) * weights
        )
        grad_bias = float(np.sum(error_vector))
        return neg_log_likelihood + reg_term, np.append(grad_weights, grad_bias)

    opt_result = minimize(
        fun=objective_and_gradient,
        x0=initial_params,
        jac=True,
        method="L-BFGS-B",
    )
    fitted_params = opt_result.x
    return fitted_params[:-1], float(fitted_params[-1])


def compute_binary_metrics(
    true_labels: NDArray[np.int64],
    predicted_probs: NDArray[np.float64],
    threshold: float = 0.5,
) -> BinaryClassificationMetrics:
    """Calcula ROC-AUC exacto por rangos, F1-Score, Precisión, Recall y Exactitud."""
    binary_preds = (predicted_probs >= threshold).astype(np.int64)
    true_positives = int(np.sum((binary_preds == 1) & (true_labels == 1)))
    false_positives = int(np.sum((binary_preds == 1) & (true_labels == 0)))
    false_negatives = int(np.sum((binary_preds == 0) & (true_labels == 1)))
    accuracy = float(np.mean(binary_preds == true_labels))

    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0.0
    )
    f1_score = (
        (2.0 * precision * recall) / (precision + recall)
        if (precision + recall) > 0.0
        else 0.0
    )

    # Cálculo vectorizado de ROC-AUC mediante estadístico de Mann-Whitney U
    sorted_indices = np.argsort(predicted_probs)
    ranks = np.empty_like(sorted_indices, dtype=np.float64)
    ranks[sorted_indices] = np.arange(1, len(predicted_probs) + 1, dtype=np.float64)
    pos_count = int(np.sum(true_labels == 1))
    neg_count = int(np.sum(true_labels == 0))
    if pos_count > 0 and neg_count > 0:
        pos_rank_sum = float(np.sum(ranks[true_labels == 1]))
        roc_auc = (
            pos_rank_sum - (pos_count * (pos_count + 1) / 2.0)
        ) / float(pos_count * neg_count)
    else:
        roc_auc = 0.5

    return BinaryClassificationMetrics(
        roc_auc=round(roc_auc, 4),
        f1_score=round(f1_score, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        accuracy=round(accuracy, 4),
    )


def fit_ridge_time_regressor(
    design_matrix: NDArray[np.float64],
    hours_targets: NDArray[np.float64],
    ridge_alpha: float = 2.2,
) -> tuple[NDArray[np.float64], float]:
    """Ajusta un regresor Ridge en escala log-horas para estimar tiempo al impacto."""
    log_targets = np.log1p(np.clip(hours_targets, 0.5, 72.0))
    target_mean = float(np.mean(log_targets))
    centered_targets = log_targets - target_mean

    feature_dim = design_matrix.shape[1]
    gram_matrix = (design_matrix.T @ design_matrix) + (
        ridge_alpha * np.eye(feature_dim, dtype=np.float64)
    )
    weights = np.linalg.solve(gram_matrix, design_matrix.T @ centered_targets)
    return weights, target_mean


def predict_hours_from_ridge(
    design_matrix: NDArray[np.float64],
    reg_weights: NDArray[np.float64],
    reg_bias: float,
) -> NDArray[np.float64]:
    """Predice horas estimadas hasta el evento revirtiendo la transformación log1p."""
    log_predictions = (design_matrix @ reg_weights) + reg_bias
    return np.clip(np.expm1(log_predictions), 0.8, 72.0)


@lru_cache(maxsize=1)
def get_trained_catastrophe_model() -> TrainedCatastropheArtifacts:
    """Entrena, compara y valida el pipeline ML una sola vez al iniciar el servicio."""
    try:
        dataset = load_historical_moche_fen_dataset()
        total_rows = dataset.raw_feature_matrix.shape[0]
        total_missing = int(np.isnan(dataset.raw_feature_matrix).sum())

        # 1. Partición estrictamente cronológica: 70% Train / 15% Val / 15% Test
        train_end = int(total_rows * 0.70)
        val_end = int(total_rows * 0.85)

        raw_x_train = dataset.raw_feature_matrix[:train_end]
        raw_x_val = dataset.raw_feature_matrix[train_end:val_end]
        raw_x_test = dataset.raw_feature_matrix[val_end:]

        y_train = dataset.catastrophe_labels[:train_end]
        y_val = dataset.catastrophe_labels[train_end:val_end]
        y_test = dataset.catastrophe_labels[val_end:]

        hours_train = dataset.hours_to_impact_targets[:train_end]
        hours_test = dataset.hours_to_impact_targets[val_end:]

        # 2. Imputación y estandarización ajustadas EXCLUSIVAMENTE en Train
        preprocessor = fit_train_only_preprocessor(
            raw_train_features=raw_x_train,
            total_dataset_missing=total_missing,
        )
        x_train_scaled = transform_features_matrix(raw_x_train, preprocessor)
        x_val_scaled = transform_features_matrix(raw_x_val, preprocessor)
        x_test_scaled = transform_features_matrix(raw_x_test, preprocessor)

        # 3. Modelo Base A: Regresión Logística Regularizada L2
        base_weights, base_bias = fit_l2_logistic_classifier(
            design_matrix=x_train_scaled,
            binary_targets=y_train,
            l2_penalty=1.0,
        )
        val_probs_base = expit((x_val_scaled @ base_weights) + base_bias)
        test_probs_base = expit((x_test_scaled @ base_weights) + base_bias)
        val_metrics_base = compute_binary_metrics(y_val, val_probs_base)
        test_metrics_base = compute_binary_metrics(y_test, test_probs_base)

        # 4. Modelo Candidato B: Clasificador No-Lineal RBF Hidrológico (RFF + L2)
        rff_rng = np.random.default_rng(seed=202699)
        rff_components = 42
        rff_omega = rff_rng.normal(
            loc=0.0,
            scale=0.62,
            size=(len(FEATURE_COLUMN_NAMES), rff_components),
        )
        rff_phase = rff_rng.uniform(0.0, 2.0 * np.pi, size=(1, rff_components))

        x_train_rff = project_random_fourier_features(
            x_train_scaled, rff_omega, rff_phase
        )
        x_val_rff = project_random_fourier_features(x_val_scaled, rff_omega, rff_phase)
        x_test_rff = project_random_fourier_features(
            x_test_scaled, rff_omega, rff_phase
        )

        rff_weights, rff_bias = fit_l2_logistic_classifier(
            design_matrix=x_train_rff,
            binary_targets=y_train,
            l2_penalty=1.35,
        )
        val_probs_rff = expit((x_val_rff @ rff_weights) + rff_bias)
        test_probs_rff = expit((x_test_rff @ rff_weights) + rff_bias)
        val_metrics_rff = compute_binary_metrics(y_val, val_probs_rff)
        test_metrics_rff = compute_binary_metrics(y_test, test_probs_rff)

        # Selección objetiva en el conjunto de Validación
        use_nonlinear = (val_metrics_rff.roc_auc + val_metrics_rff.f1_score) >= (
            val_metrics_base.roc_auc + val_metrics_base.f1_score
        )
        selected_test_metrics = (
            test_metrics_rff if use_nonlinear else test_metrics_base
        )

        # 5. Regresor No-Lineal de Tiempo hasta Impacto (evaluado en Test con MAE/RMSE)
        time_weights, time_bias = fit_ridge_time_regressor(
            design_matrix=x_train_rff,
            hours_targets=hours_train,
            ridge_alpha=2.4,
        )
        test_pred_hours = predict_hours_from_ridge(
            design_matrix=x_test_rff,
            reg_weights=time_weights,
            reg_bias=time_bias,
        )
        test_mae_hours = float(np.mean(np.abs(test_pred_hours - hours_test)))
        test_rmse_hours = float(
            np.sqrt(np.mean((test_pred_hours - hours_test) ** 2))
        )

        selected_name = (
            "Clasificador No-Lineal Kernel RBF Hidrológico"
            if use_nonlinear
            else "Regresión Logística Regularizada (L2)"
        )
        summary = MlModelValidationSummary(
            selected_model_name=selected_name,
            baseline_model_name="Regresión Logística L2 Base",
            train_samples=int(train_end),
            validation_samples=int(val_end - train_end),
            test_samples=int(total_rows - val_end),
            missing_values_imputed=total_missing,
            selected_roc_auc=round(selected_test_metrics.roc_auc, 3),
            baseline_roc_auc=round(test_metrics_base.roc_auc, 3),
            selected_f1_score=round(selected_test_metrics.f1_score, 3),
            baseline_f1_score=round(test_metrics_base.f1_score, 3),
            time_regressor_mae_hours=round(test_mae_hours, 2),
            time_regressor_rmse_hours=round(test_rmse_hours, 2),
        )

        ML_LOGGER.info(
            "Pipeline ML listo -> Modelo='%s' | Test ROC-AUC=%.3f (Base=%.3f) | "
            "F1=%.3f | Regresor Tiempo MAE=%.2fh",
            summary.selected_model_name,
            summary.selected_roc_auc,
            summary.baseline_roc_auc,
            summary.selected_f1_score,
            summary.time_regressor_mae_hours,
        )

        return TrainedCatastropheArtifacts(
            preprocessor=preprocessor,
            use_nonlinear_rff=use_nonlinear,
            selected_weights=rff_weights if use_nonlinear else base_weights,
            selected_bias=rff_bias if use_nonlinear else base_bias,
            linear_explain_weights=np.maximum(0.05, np.abs(base_weights)),
            rff_omega=rff_omega,
            rff_phase=rff_phase,
            time_reg_weights=time_weights,
            time_reg_bias=time_bias,
            validation_summary=summary,
        )
    except (ValueError, np.linalg.LinAlgError) as exc:
        ML_LOGGER.error("Fallo entrenando modelo predictivo de catástrofes: %s", exc)
        raise MlPipelineTrainingError(
            f"No fue posible ajustar el modelo predictivo ML: {exc}"
        ) from exc


def _score_feature_matrix(
    raw_matrix: NDArray[np.float64],
    artifacts: TrainedCatastropheArtifacts,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Ejecuta inferencia vectorizada de probabilidad [0-1] y horas hasta impacto."""
    scaled_matrix = transform_features_matrix(raw_matrix, artifacts.preprocessor)
    rff_matrix = project_random_fourier_features(
        scaled_matrix, artifacts.rff_omega, artifacts.rff_phase
    )
    if artifacts.use_nonlinear_rff:
        probs = expit((rff_matrix @ artifacts.selected_weights) + artifacts.selected_bias)
    else:
        probs = expit(
            (scaled_matrix @ artifacts.selected_weights) + artifacts.selected_bias
        )
    est_hours = predict_hours_from_ridge(
        design_matrix=rff_matrix,
        reg_weights=artifacts.time_reg_weights,
        reg_bias=artifacts.time_reg_bias,
    )
    return probs, est_hours


def _build_window_and_action_labels(
    probability_pct: float,
    estimated_hours: float,
) -> tuple[str, float | None, str, str]:
    """Traduce la salida numérica del modelo a mensajes operativos claros."""
    if probability_pct >= 80.0:
        clamped_hours = round(max(0.8, min(3.8, estimated_hours)), 1)
        return (
            "INMINENTE",
            clamped_hours,
            f"Impacto catastrófico estimado en ~{clamped_hours} horas",
            "Cerrar tránsito en Puente Río Moche y desviar flota INDECI por ruta alta PE-10A.",
        )
    if probability_pct >= 55.0:
        clamped_hours = round(max(3.5, min(11.5, estimated_hours)), 1)
        return (
            "ALTO",
            clamped_hours,
            f"Riesgo alto de desborde en próximas ~{clamped_hours} horas",
            "Pre-posicionar maquinaria y alistar desvío preventivo por Carretera Laredo.",
        )
    if probability_pct >= 28.0:
        clamped_hours = round(max(12.0, min(36.0, estimated_hours)), 1)
        return (
            "MODERADO",
            clamped_hours,
            f"Vigilancia activa: posible crecida en ~{clamped_hours:.0f} horas",
            "Mantener monitoreo hidrológico continuo cada 30 minutos sin cerrar vía.",
        )
    return (
        "BAJO",
        None,
        "Sin catástrofe prevista en las próximas 72 horas",
        "Corredor Panamericana Norte seguro para circulación logística normal.",
    )


def predict_catastrophe_risk(
    senamhi_telemetry: SenamhiTelemetry,
    eonet_events: tuple[NasaEonetEvent, ...],
    sentinel_reading: SentinelRadarReading,
    nlp_validation: NlpValidationResult,
) -> MlCatastrophePrediction:
    """Predice en tiempo real la probabilidad de catástrofe y cuándo podría ocurrir."""
    artifacts = get_trained_catastrophe_model()

    active_storm_severity = max(
        (evt.severity_index for evt in eonet_events if evt.is_active),
        default=0.18,
    )
    enso_sst_anomaly_c = round(
        0.55 + (active_storm_severity * 2.15) + (senamhi_telemetry.accumulated_rain_mm * 0.012),
        2,
    )
    rain_intensity_mm_h = round(
        max(
            0.4,
            (senamhi_telemetry.accumulated_rain_mm * 0.135)
            + (active_storm_severity * 2.8),
        ),
        1,
    )
    citizen_density_ratio = round(nlp_validation.credibility_percentage / 100.0, 3)

    current_vector = np.array(
        [
            [
                senamhi_telemetry.accumulated_rain_mm,
                senamhi_telemetry.river_discharge_m3s,
                sentinel_reading.soil_saturation_pct,
                rain_intensity_mm_h,
                enso_sst_anomaly_c,
                citizen_density_ratio,
            ]
        ],
        dtype=np.float64,
    )

    probs_array, hours_array = _score_feature_matrix(current_vector, artifacts)
    probability_pct = round(float(np.clip(probs_array[0] * 100.0, 1.2, 99.4)), 1)
    raw_hours = float(hours_array[0])

    risk_tier, effective_hours, window_label, action_text = _build_window_and_action_labels(
        probability_pct=probability_pct,
        estimated_hours=raw_hours,
    )

    # Proyección vectorizada multi-horizonte (+3h, +6h, +12h, +24h)
    horizons = np.array([3, 6, 12, 24], dtype=np.int64)
    trend_factor = 1.0 if senamhi_telemetry.accumulated_rain_mm >= 38.0 else -0.45
    horizon_deltas = (horizons.astype(np.float64) / 24.0) * trend_factor
    projected_matrix = np.repeat(current_vector, repeats=len(horizons), axis=0)
    projected_matrix[:, 0] = np.clip(
        projected_matrix[:, 0] + (horizon_deltas * 11.5), 1.0, 140.0
    )
    projected_matrix[:, 1] = np.clip(
        projected_matrix[:, 1] + (horizon_deltas * 58.0), 40.0, 790.0
    )
    projected_matrix[:, 2] = np.clip(
        projected_matrix[:, 2] + (horizon_deltas * 7.5), 15.0, 99.5
    )

    horizon_probs, _ = _score_feature_matrix(projected_matrix, artifacts)
    horizon_points = tuple(
        HorizonForecastPoint(
            horizon_hours=int(h_val),
            horizon_label=f"+{int(h_val)}h",
            probability_pct=round(float(np.clip(h_prob * 100.0, 1.0, 99.6)), 1),
        )
        for h_val, h_prob in zip(horizons, horizon_probs, strict=True)
    )

    # Explicabilidad local: contribución relativa de cada variable actual
    scaled_single = transform_features_matrix(current_vector, artifacts.preprocessor)[0]
    positive_push = np.maximum(0.05, scaled_single + 1.15) * artifacts.linear_explain_weights
    normalized_contrib = (positive_push / float(np.sum(positive_push))) * 100.0

    formatted_values = (
        f"{senamhi_telemetry.accumulated_rain_mm:.1f} mm",
        f"{senamhi_telemetry.river_discharge_m3s:.1f} m³/s",
        f"{sentinel_reading.soil_saturation_pct:.1f}%",
        f"{rain_intensity_mm_h:.1f} mm/h",
        f"+{enso_sst_anomaly_c:.1f} °C",
        f"{nlp_validation.credibility_percentage:.0f}%",
    )
    sorted_driver_idx = np.argsort(-normalized_contrib)[:4]
    feature_drivers = tuple(
        MlFeatureDriver(
            feature_name=HUMAN_FEATURE_LABELS[int(idx)],
            current_value_label=formatted_values[int(idx)],
            contribution_pct=round(float(normalized_contrib[int(idx)]), 1),
            is_elevated=bool(scaled_single[int(idx)] > 0.35),
        )
        for idx in sorted_driver_idx
    )

    ML_LOGGER.info(
        "Inferencia ML completada -> Probabilidad=%.1f%% [%s] | Ventana='%s'",
        probability_pct,
        risk_tier,
        window_label,
    )

    return MlCatastrophePrediction(
        probability_pct=probability_pct,
        risk_tier=risk_tier,
        is_catastrophe_likely=probability_pct >= 55.0,
        estimated_hours_to_impact=effective_hours,
        predicted_window_label=window_label,
        recommended_action=action_text,
        enso_sst_anomaly_c=enso_sst_anomaly_c,
        rain_intensity_mm_h=rain_intensity_mm_h,
        horizon_forecast=horizon_points,
        feature_drivers=feature_drivers,
        validation_summary=artifacts.validation_summary,
    )


if __name__ == "__main__":
    trained_bundle = get_trained_catastrophe_model()
    ML_LOGGER.info(
        "Validación autónoma del predictor ML exitosa: ROC-AUC=%.3f",
        trained_bundle.validation_summary.selected_roc_auc,
    )

