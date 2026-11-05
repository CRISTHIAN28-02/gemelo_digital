# 💧 Gemelo Digital — Planta de Tratamiento de Agua (PTAP/PTAR)

MVP funcional y navegable de monitoreo, análisis predictivo y apoyo a la toma
de decisiones para una planta de tratamiento de agua, con autenticación por
roles, gemelo digital interactivo, alertas, predicción de mantenimiento,
recomendación de dosificación, simulación What-If, reportes exportables,
asistente de IA basado en reglas y módulos administrativos.

## 1. Instalación y ejecución

```bash
cd gemelo_digital_mvp

# (Recomendado) entorno virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
streamlit run app.py
```

Se abre en `http://localhost:8501`. La base de datos (`database/gemelo_digital.db`,
SQLite) se crea y se puebla automáticamente con datos de demostración la
primera vez que se ejecuta la aplicación — no requiere ningún paso manual.

Usuarios y matriz de accesos: ver **`USUARIOS_Y_ACCESOS.txt`**.

Si tu versión de Streamlit es anterior a 1.36 y ves un error relacionado con
`st.Page` o `st.navigation`, actualízala con:
```bash
pip install --upgrade streamlit
```

## 2. Estructura del proyecto

```
gemelo_digital_mvp/
├── app.py                     # Entrada: login + navegación por rol
├── requirements.txt
├── USUARIOS_Y_ACCESOS.txt     # Credenciales demo y matriz de permisos
├── database/
│   └── db.py                  # Esquema SQLite, helpers de acceso y datos demo
├── services/                  # Lógica de negocio (independiente de la UI)
│   ├── auth.py                 # Login y control de acceso por rol
│   ├── auditoria.py             # Registro de auditoría
│   ├── motor_predictivo.py      # Dosificación, turbidez, costo, riesgo
│   ├── simulador.py             # Simulador de ingesta IoT (sustituye a MQTT)
│   └── asistente_ia.py          # Asistente basado en reglas + consultas SQL
└── pages/                      # Una página Streamlit por módulo del menú
    ├── 1_Dashboard.py
    ├── 2_Monitoreo.py
    ├── 3_Gemelo_Digital.py
    ├── 4_Equipos.py
    ├── 5_Alertas.py
    ├── 6_Predicciones.py
    ├── 7_Dosificacion.py
    ├── 8_Simulacion_WhatIf.py
    ├── 9_Reportes.py
    ├── 10_Asistente_IA.py
    ├── 11_Mi_Perfil.py
    ├── 12_Usuarios.py          # Solo administrador
    ├── 13_Sensores.py          # Solo administrador
    ├── 14_Configuracion.py     # Solo administrador
    └── 15_Auditoria.py         # Solo administrador
```

La carpeta `services/` concentra toda la lógica (consultas, cálculos,
reglas) separada de las páginas: cada página solo arma la interfaz y llama a
estas funciones. Esto es lo que en el documento original se pedía como
capa de "API" entre el frontend y los datos; aquí vive dentro del mismo
proceso de Streamlit, pero está aislada para poder exponerse más adelante
como endpoints REST (por ejemplo con FastAPI) sin reescribir la lógica.

## 3. Flujo de punta a punta que se puede demostrar

```
Simulador de sensores (services/simulador.py)
        ↓
Base de datos SQLite (mediciones)
        ↓
Monitoreo (gráficos por sensor y rango de tiempo)
        ↓
Detección de anomalía (motor_predictivo.calcular_riesgo_anomalia_equipo)
        ↓
Predicciones (módulo Predicciones, con recálculo bajo demanda)
        ↓
Recomendación (módulo Dosificación)
        ↓
Simulación What-If (comparación de escenarios, guardado en bitácora)
        ↓
Decisión del operador
```

Y la ruta de administración: Usuarios → Sensores → Configuración → Auditoría.

## 4. Sustituciones de tecnología frente al documento original

El documento original pedía PostgreSQL/TimescaleDB, un broker MQTT real,
backend en FastAPI/Node + frontend en React/Next.js, y un asistente de IA que
pudiera conectarse a un modelo de lenguaje. El propio documento autoriza
explícitamente sustituir tecnología no disponible en el entorno de ejecución,
manteniendo la arquitectura modular. Para este MVP:

| Requisito original                  | Sustituido por (en este MVP)                                   |
|--------------------------------------|------------------------------------------------------------------|
| PostgreSQL + TimescaleDB             | SQLite (un solo archivo, sin infraestructura adicional)          |
| Broker MQTT real + servicio de ingesta | `services/simulador.py`: genera lecturas nuevas bajo demanda o al abrir Dashboard/Monitoreo |
| Backend FastAPI/Node + frontend React| Aplicación Streamlit multipágina (`services/` = lógica, `pages/` = UI) |
| Modelo de ML entrenado para predicción| Reglas explícitas sobre las últimas lecturas, claramente marcadas como "modelo demostrativo" |
| Asistente de IA con LLM              | Asistente basado en reglas + consultas SQL (ver `services/asistente_ia.py`) |
| Hash de contraseña con bcrypt/argon2 | SHA-256 + sal fija (**solo demo**, ver nota de seguridad abajo) |

Ninguna de estas sustituciones cambia la arquitectura por capas (datos →
lógica → interfaz) ni el flujo funcional; solo el motor concreto detrás de
cada capa, tal como permite el punto 23 del documento original.

## 5. Qué NO incluye este MVP (a propósito)

Siguiendo el punto 25 del documento original ("no sobredimensionar el MVP"):

- Control autónomo de la planta (todas las recomendaciones son de apoyo a la
  decisión; nada se aplica automáticamente sobre la operación física).
- Un modelo de Machine Learning entrenado con datos reales (el riesgo de
  anomalía usa reglas simples y transparentes, explícitamente marcadas como
  demostrativas).
- Un broker MQTT real, PostgreSQL/TimescaleDB o un backend separado en REST
  (ver tabla de sustituciones arriba).
- Edición de contraseña propia, recuperación de contraseña o notificaciones
  por correo/push.
- Seguridad de nivel productivo (hash de contraseña robusto, tokens de
  sesión firmados, rate limiting, HTTPS): el foco del MVP es demostrar el
  flujo funcional completo, no endurecer la seguridad.

## 6. Próximos pasos sugeridos para evolucionar el MVP

1. Migrar `database/db.py` a PostgreSQL + TimescaleDB (las consultas SQL son
   estándar y requieren cambios menores).
2. Exponer las funciones de `services/` como endpoints REST (FastAPI) y
   dejar que Streamlit (o un frontend React) los consuma por HTTP.
3. Reemplazar `services/simulador.py` por un cliente MQTT real suscrito a
   los topics `planta/sensores/<variable>` y `planta/equipos/<equipo>`.
4. Entrenar un modelo de Machine Learning con el historial real de
   `mediciones` y `mantenimientos` para reemplazar las reglas de
   `calcular_riesgo_anomalia_equipo`.
5. Conectar `services/asistente_ia.py` a un modelo de lenguaje (por ejemplo,
   vía la API de Claude) que use las mismas consultas SQL como "herramientas",
   conservando la separación usuario → asistente → API interna → datos.
6. Reemplazar el hash de contraseña por bcrypt/argon2 y agregar expiración
   de sesión.

## 7. Agente inteligente con DeepSeek (sin servicios adicionales de pago)

La página `10_Asistente_IA` ahora funciona como agente con herramientas controladas:

- Consulta estado de planta, alertas, equipos en riesgo y mediciones.
- Consulta históricos de sensores por código.
- Ejecuta cálculos de dosificación y simulaciones What-If con el motor demostrativo existente.
- Busca metadatos de publicaciones científicas mediante OpenAlex (sin API key).
- Conserva el historial de conversación en la sesión de Streamlit.
- Permite dictar instrucciones mediante Web Speech API del navegador (Chrome/Edge). El audio no se envía a DeepSeek; el navegador devuelve el texto reconocido.

### Configurar DeepSeek

1. Crea una API key desde tu cuenta de DeepSeek.
2. Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml`.
3. Coloca la clave en `DEEPSEEK_API_KEY`.
4. Instala dependencias: `python -m pip install -r requirements.txt`.
5. Ejecuta: `python -m streamlit run app.py`.

También se admite la variable de entorno `DEEPSEEK_API_KEY`. No pegues la clave en el código ni la compartas.

### Voz

El dictado usa el reconocimiento de voz integrado del navegador, por lo que requiere un navegador compatible, permiso de micrófono y una conexión segura (HTTPS o localhost). La disponibilidad del reconocimiento depende del navegador y su proveedor; si no aparece, puedes seguir escribiendo normalmente.

### Costos y límites

- DeepSeek API: consume el saldo de la cuenta del usuario. El agente limita cada consulta a un máximo de cuatro llamadas de herramientas y conserva hasta diez mensajes recientes para controlar consumo.
- OpenAlex: búsqueda bibliográfica sin API key ni suscripción.
- No se integra Brave Search, Tavily, Whisper Cloud ni otro servicio externo de pago.

### Seguridad y alcance

El agente solo dispone de herramientas Python explícitamente autorizadas; no ejecuta SQL arbitrario, no cambia estados ni acciona equipos físicos. Las simulaciones no se guardan automáticamente. Las mediciones del proyecto son simuladas y los modelos de riesgo/dosificación son demostrativos: no deben utilizarse como instrucciones operativas reales sin calibración, pruebas de jarras y validación profesional.


## Asistente global y apariencia

La plataforma incorpora un asistente flotante en todos los módulos autenticados.
Este asistente usa el mismo agente y herramientas que el apartado «Asistente IA»,
pero responde en modo rápido (1–4 frases). El apartado «Asistente IA» conserva
el modo completo. El dictado y la lectura utilizan las capacidades de voz del
navegador (Chrome/Edge recomendados), sin un servicio adicional.

La interfaz utiliza variables del tema de Streamlit y acompaña la selección Light/Dark.

### Configuración de DeepSeek

Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y coloca
tu clave en `DEEPSEEK_API_KEY`. El archivo real de secretos no se distribuye
dentro del ZIP por seguridad.
