# 🤖 Afiliados AI Agent

**Sistema completo de marketing de afiliados basado en la estrategia: Grupos de Facebook + Hotmart**

![Version](https://img.shields.io/badge/version-1.0.0-purple)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📋 Descripción

**Afiliados AI Agent** es un asistente inteligente que implementa la estrategia completa del video **"Estrategia para vender en grupos de Facebook como Afiliado en Hotmart"**. El sistema te guía paso a paso a través de los 6 pilares fundamentales y ahora incluye **automatización real con Facebook Poster** 🐘 para publicar automáticamente en grupos de Facebook usando SeleniumBase con modo indetectable.

1. 🎯 **Fundamentos y Autoridad** — Posiciónate como experto sin desesperación
2. 📄 **Fan Page Profesional** — Construye tu marca en Facebook
3. 🔍 **Embudo de Grupos** — Filtra y selecciona los mejores grupos
4. 📊 **Contenido 80/20** — 80% valor, 20% promoción
5. 💬 **Conversión WhatsApp** — Captura leads y cierra ventas
6. ⚡ **Acción y Constancia** — Rutina diaria mañana, tarde y noche

---

## 🚀 Instalación

### Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos

```bash
# 1. Clona o descarga el proyecto
cd affiliate-ai-agent

# 2. Instala las dependencias
pip install -r requirements.txt

# 3. (Opcional) Instalar dependencia extra para Facebook Poster 🐘
pip install seleniumbase

# 4. ¡Listo! Ejecuta el agente
python run.py
```

---

## 🎮 Uso

### CLI Interactivo (Recomendado)

```bash
python run.py
```

Esto inicia el asistente interactivo en terminal con menús y paneles informativos.

### Dashboard Web

```bash
python run.py --dashboard
```

Luego abre tu navegador en: **http://localhost:5000**

### Comandos del Facebook Poster 🐘

```bash
# Configurar perfil de Chrome (solo la primera vez)
python run.py --fb-setup

# Ver estado del Facebook Poster
python run.py --fb-status

# Publicar automáticamente en grupos activos
python run.py --fb-post --fb-max 3

# Habilitar/deshabilitar (se hace desde el dashboard o CLI)
```

### Otros comandos

```bash
# Ver ayuda completa
python run.py --help

# Generar 10 ideas de contenido
python run.py --generate-ideas 10

# Exportar reporte de campaña
python run.py --export "Nombre de Campaña"

# Ver versión
python run.py --version
```

---

## 📁 Estructura del Proyecto

```
affiliate-ai-agent/
├── run.py                         # Punto de entrada principal
├── requirements.txt               # Dependencias
├── README.md                      # Documentación
├── GUIA_COMPLETA_AFILIADOS_AI_AGENT.md  # Guía completa + monetización
│
├── agent/                         # Núcleo del agente
│   ├── __init__.py
│   ├── cli.py                     # Interfaz CLI interactiva (Rich)
│   ├── strategy.py                # Motor de estrategia principal
│   ├── knowledge_base.py          # Base de conocimiento experto
│   ├── group_finder.py            # Buscador y filtro de grupos
│   ├── content_planner.py         # Planificador de contenido 80/20
│   ├── lead_tracker.py            # Gestión de leads WhatsApp
│   ├── campaign.py                # Gestión de campañas
│   └── database.py                # Base de datos SQLite ACID
│
├── dashboard/                     # Dashboard Web (Flask + Chart.js)
│   ├── api.py                     # API Flask (+ endpoints FB Poster)
│   ├── index.html                 # Interfaz web (+ vista FB Poster)
│   ├── style.css                  # Estilos (tema oscuro)
│   └── app.js                     # Lógica frontend + Chart.js
│
└── automation/                    # Automatización
    ├── __init__.py
    ├── facebook_poster.py         # 🐘 Publicación automática (SeleniumBase)
    ├── scheduler.py               # Planificador de rutina diaria
    └── reporter.py                # Generador de reportes
```

---

## 🧠 Los 6 Pilares de la Estrategia

### 1. 🎯 Fundamentos y Autoridad
- Define tu nicho de mercado
- Crea contenido que demuestre expertise
- Desarrolla habilidades de persuasión

### 2. 📄 Fan Page Profesional
- Crea una Fan Page (no uses perfil personal)
- Diseña logo y portada profesional
- Publica valor antes de promocionar

### 3. 🔍 Embudo de Grupos
- Busca grupos con palabras clave específicas
- Únete a 20-30 grupos como mínimo
- Prueba cada grupo con contenido de valor primero
- Filtra: quédate solo con los que funcionan

### 4. 📊 Contenido 80/20
- **80% Valor**: tips, tutoriales, casos de éxito
- **20% Promoción**: reseñas, ofertas, comparativas
- Usa un calendario semanal estructurado

### 5. 💬 Conversión WhatsApp
- Usa enlaces **wa.me** personalizados (con código de país)
- Prepara un guión de ventas profesional
- Da seguimiento personalizado
- Maneja objeciones comunes

### 6. ⚡ Acción y Constancia
- **Mañana**: Publica contenido de valor
- **Tarde**: Interactúa y responde
- **Noche**: Revisa métricas y planifica
- Constancia por 21 días para crear el hábito

---

## 📊 Dashboard Web

El dashboard web ofrece una interfaz visual con:

- **📊 Dashboard principal** — Cards de resumen + gráficos Chart.js
- **📦 Campañas** — CRUD completo con barra de progreso
- **🔍 Grupos** — Pipeline visual + búsqueda por keywords
- **📊 Contenido 80/20** — Estadísticas + calendario semanal
- **💬 Leads** — Pipeline de ventas + tracking WhatsApp
- **🧠 Knowledge Base** — Psicología, frases, guiones, nichos
- **🐘 Facebook Poster** — Stats, configuración, acciones, log de publicaciones
- **⚙️ Configuración** — Formulario de configuración

---

## 🐘 Facebook Poster — Automatización Real

Publica automáticamente contenido en grupos de Facebook usando **SeleniumBase** con modo indetectable (UC Mode).

### Características
- **Perfil Chrome persistente** — Las cookies se guardan entre sesiones
- **Modo indetectable** — SeleniumBase UC evade detección de bots
- **Límite diario configurable** — Evita parecer spam
- **Delays aleatorios** — Comportamiento humano simulado
- **Rotación de grupos** — No publica al mismo grupo muy seguido
- **Logging completo** — Todas las acciones quedan registradas

### Comandos

```bash
# 1. Configurar perfil de Chrome (solo primera vez)
python run.py --fb-setup

# 2. Ver estado
python run.py --fb-status

# 3. Publicar automáticamente
python run.py --fb-post --fb-max 3
```

### Flujo de trabajo

```
1. Ejecuta --fb-setup → Se abre Chrome → Inicia sesión manual (1 vez)
2. Las cookies se guardan en ~/.affiliate_agent/chrome_profile/
3. Ejecuta --fb-post → Publica en los grupos ACTIVOS del sistema
4. Revisa resultados en el Dashboard (sección 🐘 Facebook Poster)
```

> ⚠️ **IMPORTANTE:** Solo publica en grupos marcados como "Activos" en el sistema.
> Asegúrate de tener grupos activos antes de usar --fb-post.

## 🔧 Otras Automatizaciones

### Planificador Diario
```bash
python -m automation.scheduler --today    # Plan del día
python -m automation.scheduler --week     # Plan semanal
python -m automation.scheduler --report   # Reporte detallado
```

### Generador de Reportes
```bash
python -m automation.reporter --daily                        # Resumen diario
python -m automation.reporter --campaign "Mi Campaña"        # Reporte semanal
python -m automation.reporter --campaign "Mi Campaña" --markdown  # Exportar MD
```

---

## 🔑 Nichos Recomendados

| Nicho | Nivel | Descripción |
|-------|-------|-------------|
| Finanzas Personales | 🔥🔥🔥🔥🔥 | Ahorro, inversiones, criptomonedas |
| Salud y Fitness | 🔥🔥🔥🔥🔥 | Pérdida de peso, ejercicios, nutrición |
| Marketing Digital | 🔥🔥🔥🔥🔥 | Redes sociales, embudos, publicidad |
| Desarrollo Personal | 🔥🔥🔥🔥 | Productividad, hábitos, mentalidad |
| Negocios Online | 🔥🔥🔥🔥🔥 | Ecommerce, dropshipping, afiliados |
| Habilidades Técnicas | 🔥🔥🔥🔥 | Programación, diseño, edición |
| Idiomas | 🔥🔥🔥🔥 | Inglés, métodos de aprendizaje |
| Relaciones | 🔥🔥🔥🔥 | Comunicación, autoestima |

---

## 📈 Métricas Clave

1. **Posts publicados por día** — Mide tu constancia
2. **Comentarios por post** — Mide engagement real
3. **Leads captados por WhatsApp** — Mide conversión
4. **Tasa de cierre** — leads → ventas
5. **Grupos activos** — Mide tu alcance
6. **Ingresos semanales** — Mide resultados económicos

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Haz fork del proyecto
2. Crea una rama para tu feature
3. Envía un Pull Request

---

## 📝 Licencia

MIT License — Ver archivo `LICENSE` para más detalles.

---

## 🙏 Créditos

Basado en la estrategia del video: **"Estrategia para vender en grupos de Facebook como Afiliado en HOTMART"**

---

<p align="center">
  <b>🚀 La constancia es la clave del éxito</b><br>
  <small>Hecho con ❤️ para afiliados de Hotmart</small>
</p>
