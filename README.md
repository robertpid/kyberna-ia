# 🌊 Kyberna IA — Centro de Mando Logístico Inteligente ante el Fenómeno del Niño

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/Frontend-React%2019%20+%20Vite-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Leaflet](https://img.shields.io/badge/GIS-Leaflet.js%20+%20OSRM-199900?style=flat&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean%20N--Tier-blue.svg)](#)
[![Python 3.12](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Kyberna IA** es un sistema full-stack de alerta temprana, auditoría de campo con web scraping y ruteo logístico de emergencia diseñado para mitigar el impacto humanitario y económico del **Fenómeno del Niño** en el Perú. 
> Implementa un **Pipeline Autónomo de 4 Etapas**, cálculo de damnificados basado en normas **EDAN / CENEPRED** y desvío vial dinámico con **Dijkstra sobre carreteras reales (OpenStreetMap / OSRM)** en la cuenca del Río Moche (La Libertad).

📄 **Dossier Técnico Ejecutivo en PDF:** [Descargar Kyberna_IA_Dossier_Tecnico.pdf](Kyberna_IA_Dossier_Tecnico.pdf)  
🔗 **Repositorio Oficial en GitHub:** [https://github.com/robertpid/kyberna-ia](https://github.com/robertpid/kyberna-ia)

---

## 📑 Tabla de Contenidos

1. [Problema y Solución](#-problema-y-solución)
2. [Pipeline Autónomo de 4 Etapas](#-pipeline-autónomo-de-4-etapas)
3. [Arquitectura de Software (N-Capas)](#-arquitectura-de-software-n-capas)
4. [Modelo Hidrológico de Damnificados y Suministros (EDAN / SPHERE)](#-modelo-hidrológico-de-damnificados-y-suministros-edan--sphere)
5. [Guía de Despliegue Multidispositivo](#-guía-de-despliegue-multidispositivo)
   - [Opción A: Ejecución Local Rápida (Misma PC)](#opción-a-ejecución-local-rápida-misma-pc)
   - [Opción B: Abrir en Celulares y Tablets (Misma Red WiFi)](#opción-b-abrir-en-celulares-y-tablets-misma-red-wifi)
   - [Opción C: Desplegar en Otra Computadora / Laptop (Windows, Linux, macOS)](#opción-c-desplegar-en-otra-computadora--laptop-windows-linux-macos)
   - [Opción D: Despliegue con Docker / Docker Compose (1 solo comando)](#opción-d-despliegue-con-docker--docker-compose-1-solo-comando)
   - [Opción E: Despliegue en la Nube (Render, Railway, VPS)](#opción-e-despliegue-en-la-nube-render-railway-vps)
6. [Escalabilidad Nacional](#-escalabilidad-nacional)
7. [Modelo de Negocio y Monetización (B2G y B2B)](#-modelo-de-negocio-y-monetización-b2g-y-b2b)
8. [Auditoría de Código Limpio y Verificación](#-auditoría-de-código-limpio-y-verificación)

---

## 🎯 Problema y Solución

| El Problema Actual (Fenómeno del Niño) | La Solución de Kyberna IA |
| :--- | :--- |
| **Alertas Tardías o Alarmistas:** Reportes meteorológicos genéricos generan pánico o desatención ciudadana. | **Avisos Informativos Graduales:** Alertas tempranas no alarmistas vía Telegram y WhatsApp enfocadas en prevención. |
| **Ceguera Logística en Carreteras:** Convoyes de INDECI y flotas comerciales quedan varados en puentes colapsados. | **Desvíos Viales en Tiempo Real:** Algoritmo Dijkstra sobre polilíneas reales (OSRM) para desvío seguro por rutas alternas (ej. PE-10A Laredo). |
| **Estimaciones a Ciegas:** El conteo oficial de damnificados (ficha EDAN) tarda entre 48 y 72 horas tras el huaico. | **Estimación Inmediata Instantánea:** Cruce de mapas censales INEI, tipo de vivienda y saturación de suelo para estimar familias, alimentos y camiones en 0 segundos. |

---

## 🔄 Pipeline Autónomo de 4 Etapas

El núcleo operacional de Kyberna IA se rige por un autómata finito de 4 fases que transiciona de forma determinista y auditable:

```mermaid
flowchart TD
    subgraph E1["Etapa 1: Vigilancia Rutinaria"]
        A1["Polling cada 15 min\nSENAMHI + NASA + Sentinel-1"]
        A2["Semáforo VERDE\nCorredor Fluvial Seguro"]
        A1 --> A2
    end

    subgraph E2["Etapa 2: Alerta Preventiva ML"]
        B1["Disparo de Modelo ML\n(Supervisado FEN 1998-2026)"]
        B2["Aviso No-Alarmista\nTelegram / WhatsApp Ciudadano"]
        B1 --> B2
    end

    subgraph E3["Etapa 3: Auditoría Web Scraping"]
        C1["Extracción de Noticias Regionales\n(RPP, La Industria, Correo)"]
        C2["Clasificación Automática:\nInundaciones, Adobe, Vías Bloqueadas"]
        C1 --> C2
    end

    subgraph E4["Etapa 4: Desvío Dijkstra y Alerta Roja"]
        D1["Cálculo Hidrológico Damnificados\n+ Raciones INDECI 72h"]
        D2["Algoritmo Dijkstra sobre OSRM\nCierre Puente Moche -> Desvío PE-10A Laredo"]
        D3["Despacho Táctico a Flota y Convoy"]
        D1 --> D2 --> D3
    end

    E1 -->|Lluvia >35mm o Caudal Anómalo| E2
    E2 -->|Impacto Pronosticado <= 4h| E3
    E3 -->|Reportes Confirmados en Terreno| E4
```

1. **Etapa 1 · Vigilancia Rutinaria (Polling 15 min):**  
   Monitoreo continuo de estaciones hidrometeorológicas. Corredor Moche expedito, semáforo en verde, contador regresivo visible para la próxima consulta.
2. **Etapa 2 · Alerta Preventiva (Disparo ML no alarmista):**  
   La telemetría supera los umbrales de alerta temprana (>35 mm/h o Niño 1+2 > 1.8°C). El modelo ML pronostica la ventana de impacto (ej. 3.5 horas) y despacha un comunicado sereno y preventivo por Telegram/WhatsApp.
3. **Etapa 3 · Web Scraping en Vivo (Auditoría de Prensa y Redes):**  
   Si el impacto se prevé en $\le 4$ horas, se activa el rastreador web (`data/web_scraping_service.py`), recolectando noticias de portales regionales (*RPP Trujillo, La Industria, Diario Correo*) y redes sociales. Clasifica evidencias en 4 categorías: Inundaciones, Estructuras de Adobe, Familias Aisladas y Vías Afectadas.
4. **Etapa 4 · Desvío Humanitario Dijkstra (Alerta Roja):**  
   Con la emergencia confirmada, el semáforo cambia a Rojo. Se bloquea el nodo del Puente Río Moche en la Panamericana Norte y Dijkstra calcula la ruta de desvío segura por la carretera PE-10A (Laredo – Simbal). Se calcula la población damnificada exacta, toneladas de ayuda requeridas y recomendaciones tácticas por rol.

---

## 🏛 Arquitectura de Software (N-Capas)

El proyecto sigue una **Arquitectura Limpia y Desacoplada**, garantizando que la lógica de negocio y los modelos matemáticos no dependan del framework web ni de librerías externas de interfaz:

```text
kyberna-ia/
├── main.py                          # Punto de entrada FastAPI + Servidor de archivos estáticos
├── Dockerfile                       # Definición de contenedor multi-arquitectura
├── docker-compose.yml               # Orquestación con 1 comando
├── requirements.txt                 # Dependencias Python bloqueadas
├── build_dossier_pdf.py             # Generador automatizado del Dossier Ejecutivo en PDF
├── verify_kyberna_pipeline.py       # Suite de verificación de código limpio (cero print, AST)
├── models/                          # Contratos de datos inmutables y schemas Pydantic
│   └── schemas.py                   # Modelos DTO: PipelineStage, Telemetry, RouteResponse
├── utils/                           # Servicios transversales
│   └── logger_config.py             # Logging centralizado formateado (INFO, WARNING, ERROR)
├── data/                            # CAPA DE ACCESO A DATOS Y FUENTES EXTERNAS
│   ├── historical_fen_dataset.py    # Matriz histórica de eventos FEN (1998, 2017, 2023, 2026)
│   ├── mock_sources.py              # Fuentes de telemetría SENAMHI, NASA EONET, Copernicus SAR
│   ├── web_scraping_service.py      # Scraper y clasificador de noticias locales y redes
│   └── osrm_road_geometries.json    # Polilíneas georreferenciadas de carreteras peruanas (OSRM)
├── logic/                           # CAPA DE REGLAS DE NEGOCIO Y MODELOS CIENTÍFICOS
│   ├── ml_catastrophe_predictor.py  # Predictor supervisado de probabilidad y ventana de tiempo
│   ├── huaico_agent.py              # Agente detector de huaicos y desbordes fluviales
│   ├── nlp_engine.py                # Clasificador de reportes ciudadanos y detección de fake news
│   ├── humanitarian_estimator.py    # Motor de cálculo de damnificados, kits INDECI y táctica
│   ├── route_calculator.py          # Motor de grafos y Dijkstra sobre redes viales
│   └── orchestrator.py              # Orquestador del ciclo de vida de las 4 etapas
├── notifications/                   # CAPA DE NOTIFICACIONES MULTICANAL
│   ├── telegram_service.py          # Integración HTTP asíncrona real con la API de Telegram
│   └── whatsapp_service.py          # Adaptador mock para mensajería instantánea empresarial
├── api/                             # CAPA DE EXPOSICIÓN HTTP REST
│   └── routes.py                    # Endpoints (/surveillance, /simulate, /stage, /notify)
└── frontend/                        # CENTRO DE MANDO EN TIEMPO REAL (REACT 19 + VITE + LEAFLET)
    ├── package.json
    ├── vite.config.js
    ├── dist/                        # Bundle de producción precompilado (servido por FastAPI)
    └── src/
        ├── App.jsx                  # Estado reactivo global y orquestación UI
        ├── styles/dashboard.css     # Hoja de estilos moderna con glassmorphism y CSS nativo
        └── components/
            ├── TopCommandBar.jsx            # Stepper de 4 etapas + contador 15 min en vivo
            ├── InteractivePeruMap.jsx       # Mapa interactivo Leaflet con polilíneas OSRM
            ├── InteractiveTabsPanel.jsx     # Auditoría Web Scraping, NLP y métricas
            ├── SurveillanceMetricsPanel.jsx # Telemetría de sensores y simulador deslizante
            └── TelegramConfigDialog.jsx     # Modal nativo para vincular Bot de Telegram
```

---

## 🧮 Modelo Hidrológico de Damnificados y Suministros (EDAN / SPHERE)

Kyberna IA no utiliza números arbitrarios. La estimación de damnificados en la **Etapa 4** se fundamenta en la matriz de vulnerabilidad física y poblacional del **CENEPRED** y el manual de evaluación de daños **EDAN - INDECI**:

$$\text{Damnificados} = \sum_{z \in Z} \left( P_z \times \frac{V_z}{100} \times F_{\text{suelo}} \times \left( \frac{\text{Lluvia}_{t}}{\text{Umbral}_{\text{colapso}}} \right) \right)$$

Donde:
- $P_z$: Población censal del sector (INEI 2017 actualizado).
- $V_z$: Porcentaje de viviendas con material precario o adobe no confinado en la ribera.
- $F_{\text{suelo}}$: Factor de saturación hídrica antecedente del suelo (determinado por radar satelital Sentinel-1 SAR).
- $\text{Umbral}_{\text{colapso}}$: Precipitación crítica de escorrentía rápida ($50\text{ mm/h}$ para la cuenca del Río Moche).

### Canasta Humanitaria Estándar (Manual Esfera / INDECI 72 Horas)
Para cada grupo de personas damnificadas, el sistema computa de forma inmediata:
- **Kits de Alimentos:** 1 kit de 18 kg por familia cada 72 horas (no perecibles, cereales, conservas).
- **Agua Segura:** 3 litros por persona por día (mínimo vital según manual Esfera).
- **Carpas Familiares:** 1 carpa de lona ignífuga de alta resistencia por cada 4.5 personas.
- **Flota Logística Requerida:** Determinación de camiones rígidos de 10 Toneladas Métricas necesarios para movilizar el tonelaje total.

---

## 🚀 Guía de Despliegue Multidispositivo

Una de las grandes ventajas de **Kyberna IA** es que el frontend ya se encuentra **precompilado en `frontend/dist/`** y es servido directamente por el backend de FastAPI. Esto significa que **en cualquier otro dispositivo solo necesitas Python o Docker, ¡sin necesidad de instalar Node.js ni compilar con npm!**

---

### Opción A: Ejecución Local Rápida (Misma PC)

1. Abre una terminal (PowerShell o CMD) en la carpeta del proyecto.
2. Inicia el servidor con el entorno virtual:
   ```powershell
   .\.venv\Scripts\python.exe main.py
   ```
3. Abre tu navegador web favorito en:
   👉 **`http://127.0.0.1:8000`**

---

### Opción B: Abrir en Celulares y Tablets (Misma Red WiFi)

Puedes controlar y visualizar el Centro de Mando desde tu teléfono inteligente, iPhone, iPad o tablet en tiempo real:

1. Asegúrate de que tu computadora y tu celular estén conectados a la **misma red WiFi**.
2. Averigua la dirección IP local de tu computadora:
   - En Windows: Abre PowerShell y escribe `ipconfig` (busca la línea *IPv4 Address*, por ejemplo `192.168.1.35`).
   - En Linux/Mac: Escribe `ifconfig` o `ip a` (por ejemplo `192.168.1.50`).
3. Inicia Kyberna IA escuchando en todas las interfaces de red (`0.0.0.0`):
   ```powershell
   .\.venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000
   ```
4. Toma tu celular, abre Chrome o Safari y escribe:
   👉 **`http://192.168.1.35:8000`** *(sustituye por la IP de tu PC)*

¡La interfaz responsive adaptará el mapa y el stepper automáticamente a la pantalla de tu móvil!

---

### Opción C: Desplegar en Otra Computadora / Laptop (Windows, Linux, macOS)

Para llevar el proyecto a una laptop de presentación, jurado o demostración:

1. **Clona el repositorio desde GitHub:**
   ```bash
   git clone https://github.com/robertpid/kyberna-ia.git
   cd kyberna-ia
   ```

2. **Crea un entorno virtual e instala dependencias:**
   - **En Windows:**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     pip install -r requirements.txt
     ```
   - **En Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     ```

3. **Inicia el sistema:**
   ```bash
   python main.py
   ```
   *(Listo: abre `http://localhost:8000`)*.

> 💡 **Nota:** No necesitas instalar Node.js ni ejecutar `npm install` en la otra máquina porque el paquete web ya está precompilado y optimizado dentro de `frontend/dist/`.

---

### Opción D: Despliegue con Docker / Docker Compose (1 solo comando)

Si la otra máquina tiene **Docker Desktop** o un servidor Linux con Docker instalado:

```bash
docker compose up --build
```

El contenedor compilará el entorno Python 3.12, expondrá el puerto `8000` con healthcheck automático y podrás acceder de inmediato en `http://localhost:8000`.

Para detener el servicio:
```bash
docker compose down
```

---

### Opción E: Despliegue en la Nube (Render, Railway, VPS)

Kyberna IA es 100% compatible con cualquier servicio PaaS en la nube:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Variables de Entorno (Opcionales):**
  - `TELEGRAM_BOT_TOKEN`: Token de tu bot de Telegram obtenido en BotFather.
  - `TELEGRAM_CHAT_ID`: ID del canal o chat de destino para las alertas.

---

## 📈 Escalabilidad Nacional

Aunque el MVP está validado y parametrizado con precisión métrica en la **Cuenca del Río Moche (La Libertad)**, la arquitectura de Kyberna IA está diseñada para escalar a nivel nacional:

```mermaid
flowchart LR
    subgraph Fuentes_Nacionales["Ingesta Nacional (25 Regiones)"]
        S1["SENAMHI (PISCO / Red Automática)"]
        S2["Copernicus Sentinel-1 SAR (Humedad Suelo)"]
        S3["CENEPRED SIGRID (Capas de Vulnerabilidad)"]
        S4["INEI (Microdatos Manzanas Censales)"]
    end

    subgraph Nucleo_Kyberna["Kyberna IA Engine"]
        N1["Vectorized GeoSpatial Clustering"]
        N2["Multi-Region OSRM Routing Engine"]
        N3["Multi-Agent Rerouting Dijkstra"]
    end

    subgraph Impacto_Territorial["Monitoreo Simultáneo"]
        R1["Piura: Cuenca Chira-Piura"]
        R2["Lambayeque: Río La Leche / Reque"]
        R3["La Libertad: Río Moche / Chicama"]
        R4["Lima Provincias: Río Rímac / Chillón"]
    end

    Fuentes_Nacionales --> Nucleo_Kyberna
    Nucleo_Kyberna --> Impacto_Territorial
```

- **Integración con CENEPRED SIGRID:** Ingesta de shapes georreferenciados de zonas críticas a nivel nacional para evaluar quebradas en Piura, Tumbes, Lambayeque, Ancash y Lima.
- **Rutas OSRM Multirregionales:** Sustitución del archivo local de polilíneas por una instancia de OSRM nacional con el archivo `.osm.pbf` de todo el Perú, permitiendo ruteo dinámico en la Carretera Central y la Panamericana Sur.
- **API Nacional Abierta:** Exposición de endpoints para que municipalidades provinciales y empresas de transporte consuman desvíos en formato GeoJSON en sus propios sistemas ERP o apps móviles.

---

## 💼 Modelo de Negocio y Monetización (B2G y B2B)

Kyberna IA cuenta con un modelo de doble vertiente comercial de alto impacto:

```text
+---------------------------------------------------------------------------------+
|                               MODELO DE MONETIZACIÓN                            |
+---------------------------------------------------------------------------------+
|  B2G (Gobierno y Sector Público)       |  B2B (Empresas Privadas y Logística)   |
|  - Clientes: INDECI, Gobiernos Regio-  |  - Clientes: Minería, Agroexportación, |
|    nales, Provías, COEN.               |    flotas de carga pesada en ruta.     |
|  - Propuesta: Reducción del tiempo de  |  - Propuesta: Evita pérdidas de hasta  |
|    evaluación de 72h a 0h; despacho    |    $50,000 USD/día por camión varado;  |
|    preciso y auditado de ayuda.        |    garantiza seguridad de la carga.    |
|  - Modalidad: Licencia SaaS anual por  |  - Modalidad: Suscripción mensual por  |
|    cuenca o departamento monitoreado.  |    camión activo con telemetría API.   |
+---------------------------------------------------------------------------------+
```

---

## 🛡 Auditoría de Código Limpio y Verificación

Kyberna IA cumple con los más rigurosos estándares de ingeniería de software:
- **Cero llamadas a `print()` en producción:** Toda la trazabilidad se ejecuta a través del módulo estándar `logging` con formateo profesional y niveles semánticos (`INFO`, `WARNING`, `ERROR`).
- **Tipado Estático Estricto:** Código validado con anotaciones de tipo completas en Python (`typing`).
- **Eficiencia Vectorizada:** Procesamiento numérico con NumPy y SciPy sin iteraciones lentas (`iterrows()` prohibido).
- **Suite de Verificación Automática:** Incluye un script de validación que inspecciona el árbol sintáctico (AST) y simula el pipeline completo:

```powershell
.\.venv\Scripts\python.exe verify_kyberna_pipeline.py
```

Salida esperada:
```text
[OK] AST Audit: 0 llamadas a print() encontradas en el código base.
[OK] Etapa 1: Polling normal y semáforo verde verificado.
[OK] Etapa 2: Disparo de modelo predictivo ML validado.
[OK] Etapa 3: Web scraping y categorización de noticias validada.
[OK] Etapa 4: Desvío Dijkstra y cálculo de damnificados validado.
[EXITO] Kyberna IA cumple al 100% con los estándares de ingeniería y gobernanza.
```

---

## 👥 Equipo y Créditos

Desarrollado para la Hackathon de Respuesta a Emergencias y el Fenómeno del Niño en el Perú.  
**Repositorio GitHub:** [robertpid/kyberna-ia](https://github.com/robertpid/kyberna-ia)  
**Documento Técnico:** Consulta el [Dossier Técnico Ejecutivo en PDF](Kyberna_IA_Dossier_Tecnico.pdf) para la justificación matemática y arquitectónica completa.
