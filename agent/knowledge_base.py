"""
affiliate-ai-agent/agent/knowledge_base.py
Knowledge base with expert tips, persuasion phrases, and proven strategies
for Hotmart affiliate marketing in Facebook groups.
"""


class KnowledgeBase:
    """
    Curated knowledge from the video and affiliate marketing best practices.
    Provides actionable advice, templates, and scripts.
    """

    # ─── Psicología de Venta ─────────────────────────────────────────────

    SALES_PSYCHOLOGY_TIPS = [
        "La gente compra emociones y justifica con lógica. Apela a sus deseos y miedos.",
        "El 'dolor' es el motor de compra más fuerte. Identifica el problema que resuelve el producto.",
        "La prueba social vende: 'más de 5000 estudiantes satisfechos' genera confianza.",
        "La escasez funciona: 'plazas limitadas', 'oferta por tiempo limitado'.",
        "La reciprocidad: da valor primero, y la gente querrá devolverte el favor.",
        "La autoridad: posicionarte como experto hace que te crean más fácilmente.",
        "El 'por qué': siempre explica POR QUÉ tu producto es la mejor solución.",
        "Las objeciones son oportunidades. Anticípalas y resuélvelas antes de que surjan."
    ]

    # ─── Frases para Engagement ──────────────────────────────────────────

    ENGAGEMENT_PHRASES = {
        "gancho": [
            "¿Sabías que el 90% de los emprendedores cometen este error?",
            "Te voy a contar algo que nadie te dice sobre...",
            "Si estás empezando, esto te interesa...",
            "Lo que nadie te enseña sobre vender afiliados...",
            "El error #1 que cometen los afiliados novatos...",
        ],
        "llamada_accion": [
            "Comenta 'INFO' y te envío los detalles por WhatsApp",
            "Déjame un '🔥' si quieres saber más",
            "Escríbeme al WhatsApp (link en mi bio) y te explico sin compromiso",
            "¿Te interesa? Te comparto la información por interno",
            "Mándame un mensaje directo y te cuento cómo funciona"
        ],
        "cierre": [
            "La decisión es tuya, pero la oportunidad es ahora.",
            "Invertir en conocimiento es lo único que nadie te puede quitar.",
            "El mejor momento fue ayer. El segundo mejor momento es hoy.",
            "No dejes que el miedo te detenga. Pruébalo y decide.",
            "Tu futuro yo te lo va a agradecer."
        ]
    }

    # ─── Tipos de Contenido de Valor ─────────────────────────────────────

    VALUE_CONTENT_TYPES = [
        {
            "tipo": "Tips rápidos",
            "ejemplo": "5 tips para aumentar tus ventas como afiliado hoy mismo",
            "formato": "Lista corta"
        },
        {
            "tipo": "Tutoriales",
            "ejemplo": "Cómo crear un embudo de ventas en 10 minutos",
            "formato": "Paso a paso"
        },
        {
            "tipo": "Casos de estudio",
            "ejemplo": "Cómo generé mis primeras $500 como afiliado",
            "formato": "Historia personal"
        },
        {
            "tipo": "Tendencias",
            "ejemplo": "Las 3 tendencias de marketing digital para este año",
            "formato": "Análisis"
        },
        {
            "tipo": "Mitos vs Realidad",
            "ejemplo": "Mito: 'Necesitas miles de seguidores para vender' - Realidad: 'La clave es la segmentación'",
            "formato": "Comparativo"
        },
        {
            "tipo": "Preguntas frecuentes",
            "ejemplo": "¿Cuánto dinero se necesita para empezar en afiliados?",
            "formato": "Q&A"
        },
        {
            "tipo": "Herramientas recomendadas",
            "ejemplo": "Las 5 herramientas gratis que uso como afiliado",
            "formato": "Lista con reseña"
        },
        {
            "tipo": "Errores comunes",
            "ejemplo": "Los 7 errores que matan tus ventas como afiliado",
            "formato": "Advertencia / aprendizaje"
        }
    ]

    # ─── Estrategia de Publicación ────────────────────────────────────────

    POSTING_STRATEGY = {
        "momento_dia": {
            "mañana": "7:00 - 9:00 AM: Contenido inspiracional o tips rápidos",
            "tarde": "12:00 - 2:00 PM: Contenido educativo o tutorial",
            "noche": "7:00 - 9:00 PM: Contenido promocional o historias"
        },
        "frecuencia_recomendada": [
            "Mínimo 1 post de valor por grupo cada 2 días",
            "Máximo 1 post promocional por grupo por semana",
            "Interactúa en otros posts (comenta valor) al menos 5 veces al día"
        ],
        "mejores_dias": [
            "Martes y Juegos: mejores días para contenido promocional",
            "Domingo: mejor día para contenido inspiracional",
            "Lunes: buen día para tips y consejos"
        ]
    }

    # ─── Tips de Warm Up para Grupos ────────────────────────────────────

    GROUP_WARMUP_TIPS = [
        "Los primeros 3 días solo comenta en posts existentes, no publiques",
        "Día 4-7: publica 1 post de valor (sin promocionar nada)",
        "Día 8-10: publica otro post de valor y comenta en otros posts",
        "Día 11+: si el grupo lo permite, publica tu primer post promocional",
        "Sé auténtico. La gente detecta cuando eres un bot o un spammer."
    ]

    # ─── Guión de WhatsApp ───────────────────────────────────────────────

    WHATSAPP_SCRIPT = {
        "saludo_inicial": (
            "¡Hola [nombre]! Gracias por tu interés en [producto]. "
            "Quiero contarte un poco más sobre cómo funciona y ver si es lo que buscas. "
            "¿Tienes 5 minutos para que te explique?"
        ),
        "descubrimiento": (
            "Cuéntame, ¿qué es lo que más te gustaría lograr con [tema del producto]? "
            "Así puedo contarte si esto es lo que necesitas."
        ),
        "presentacion_valor": (
            "Mira, [producto] te ayuda a [beneficio principal]. "
            "Lo que más valoran mis alumnos es [feature destacado]. "
            "Además, incluye [bonos/garantía]."
        ),
        "manejo_objecciones": {
            "precio": "Entiendo tu preocupación. Piensa que es una inversión que se recupera con la primera venta. Además, tiene garantía de [X] días.",
            "tiempo": "El programa está diseñado para personas ocupadas. Solo necesitas [X] minutos al día.",
            "resultados": "Hay casos de éxito de personas que empezaron desde cero. ¿Te comparto algunos testimonios?",
            "experiencia": "No necesitas experiencia previa. Todo está explicado desde cero, paso a paso."
        },
        "cierre": (
            "Mira, te hago una propuesta: pruébalo por [X] días. "
            "Si no ves resultados, te devuelven tu dinero. "
            "La garantía cubre cualquier riesgo. ¿Qué te parece si lo intentas?"
        )
    }

    # ─── Nichos Rentables ────────────────────────────────────────────────

    PROFITABLE_NICHES = [
        {"nombre": "Finanzas Personales", "nivel": "🔥🔥🔥🔥🔥",
         "descripcion": "Ahorro, inversiones, criptomonedas, libertad financiera"},
        {"nombre": "Salud y Fitness", "nivel": "🔥🔥🔥🔥🔥",
         "descripcion": "Pérdida de peso, ejercicios en casa, alimentación saludable"},
        {"nombre": "Desarrollo Personal", "nivel": "🔥🔥🔥🔥",
         "descripcion": "Productividad, hábitos, mentalidad, liderazgo"},
        {"nombre": "Marketing Digital", "nivel": "🔥🔥🔥🔥🔥",
         "descripcion": "Redes sociales, email marketing, embudos de venta"},
        {"nombre": "Habilidades Técnicas", "nivel": "🔥🔥🔥🔥",
         "descripcion": "Programación, diseño, edición de video, Excel"},
        {"nombre": "Relaciones y Pareja", "nivel": "🔥🔥🔥🔥",
         "descripcion": "Seducción, comunicación en pareja, autoestima"},
        {"nombre": "Negocios Online", "nivel": "🔥🔥🔥🔥🔥",
         "descripcion": "Ecommerce, dropshipping, afiliados, SaaS"},
        {"nombre": "Idiomas", "nivel": "🔥🔥🔥🔥",
         "descripcion": "Inglés, portugués, métodos de aprendizaje rápido"},
    ]

    # ─── Métricas Clave a Seguir ─────────────────────────────────────────

    KEY_METRICS = [
        {"metrica": "Posts publicados por día", "porque": "Mide tu constancia"},
        {"metrica": "Comentarios por post", "porque": "Mide engagement real"},
        {"metrica": "Leads captados por WhatsApp por día", "porque": "Mide conversión"},
        {"metrica": "Tasa de cierre (leads → ventas)", "porque": "Mide efectividad de tu script"},
        {"metrica": "Grupos activos (donde publicas)", "porque": "Mide tu alcance"},
        {"metrica": "Ingresos semanales", "porque": "Mide resultados económicos"}
    ]

    @classmethod
    def get_random_tip(cls, category: str = "general") -> str:
        """Get a random tip from a category."""
        import random
        tips = {
            "sales": cls.SALES_PSYCHOLOGY_TIPS,
            "engagement": list(cls.ENGAGEMENT_PHRASES.keys()),
            "value": [t["tipo"] for t in cls.VALUE_CONTENT_TYPES],
            "general": cls.SALES_PSYCHOLOGY_TIPS + cls.GROUP_WARMUP_TIPS
        }
        pool = tips.get(category, tips["general"])
        return random.choice(pool) if pool else "Sigue construyendo autoridad día a día."

    @classmethod
    def get_niche_recommendation(cls) -> str:
        """Get a formatted niche recommendation."""
        import random
        niche = random.choice(cls.PROFITABLE_NICHES)
        return (
            f"{niche['nivel']} {niche['nombre']}: {niche['descripcion']}"
        )
