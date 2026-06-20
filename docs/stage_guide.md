# FCSTN — Stage Demo Guide
## ESCOM Summer School | July 3

---

## Setup (5 min before)

1. **Open Unity** with FCSTNProject, verify scene loads
2. **Open 3 terminals**:
   - Terminal 1: `python deploy_server.py` (Render-style local)
   - Terminal 2: `python -m bci.brain_server --source recorded` (or `--source muse` if hardware)
   - Terminal 3: `cd flutter_app && flutter run -d chrome` (local)
3. Darken room. Set projector to 1080p. Sound on speakers.

---

## Script (30 min)

### Fase 1: El Silencio del Sistema (0:00 – 5:00)
**Load = 0.10 | Estado: resting | Color: violeta**

> **Tú:** "Lo que ven en pantalla es la FCSTN en un estado de homeostasis cognitiva pura. El entorno virtual está en equilibrio con el observador."

- Unity muestra nodos azules estables, rotación lenta, sin glitch
- Flutter sidebar: gauges en reposo, fractal sereno
- Sin input de voz

**Demo actions:**
- Señala el fractal: "Dimensión fractal en reposo: 2.3 — el espacio-tiempo virtual respira"
- Muestra los gauges: "Cada medidor representa un canal de la red neuronal adaptativa"

---

### Fase 2: El Despertar (5:00 – 12:00)
**Keyword: "viaje" → Load = 0.40 | Estado: engaged → curioso**

> **Tú:** "En el momento en que introduzco una semilla abstracta, la red calcula la dimensión fractal necesaria para albergar ese concepto en el espacio-tiempo virtual."

**Demo actions:**
- Di "viaje" o haz clic en el botón Voice Nexus
- Observa: fractal se expande suavemente, colores transicionan a morado/teal
- El LineRenderer en Unity (gráfico tipo ECG) empieza a oscilar arriba/abajo
- Los números en la UI del Flutter aumentan gradualmente

**Keywords opcionales:** "curioso", "mente", "conexion"

> **Tú:** "La red adapta su geometría a la complejidad semántica del input. Más abstracción = más dimensiones fractales."

---

### Fase 3: El Caos Absoluto (12:00 – 20:00)
**Keyword: "explosion" → Load = 0.95 | Estado: focused/stressed | Color: rojo**

> **Tú:** "Pero si el flujo de información satura el canal cognitivo, la geometría colapsa en un estado de caos adaptativo."

**Demo actions:**
- Di "explosion" con energía
- Unity: partículas explotan, glitch FULL, aberración cromática, cámara shake, terminal rain se activa
- Shader: RGB split máximo, block displacement, scanlines intensas
- Flutter: gauges en rojo, fractal en modo caótico, crossfade rápido entre renders
- El audio sube de tono: "La IA está reconfigurando las fronteras del entorno en tiempo real"

**Demo rápida opcional:** "estres", "colapso", "agresivo" — cada uno varía matices

> **Tú:** "Cada comando de voz altera la red en milisegundos. No hay latencia. El sistema respira con el usuario."

---

### Fase 4: La Calma (20:00 – 25:00)
**Keyword: "calma" → Load = 0.10 | Estado: resting**

> **Tú:** "Pero el verdadero poder no es el caos. Es la resiliencia."

**Demo actions:**
- Di "calma" suavemente
- Transición orgánica: glitch se disipa en 2-3 segundos, partículas se serenan, color vuelve a azul/violeta
- Flutter: crossfade lento hacia fractal sereno
- Gráfico de dimensión fractal se aplana

> **Tú:** "La red regresa a su estado basal. Homeostasis cognitiva. El sistema no se rompe — se adapta."

---

### Fase 5: Cierre (25:00 – 30:00)

> **Tú:** "Esto que han visto es FCSTN — Fractal Cognitive State Tuning Network. Una arquitectura que demuestra cómo el software puede leer, interpretar y visualizar el estado cognitivo humano en tiempo real."

**Demo actions:**
- Congela el fractal en un estado sereno (más violeta, simétrico)
- Abre `https://github.com/FernandoMay/fcstn` en el proyector
- Muestra QR code del repo en pantalla (preparar en docs/qr.png)

> **Tú:** "El código está abierto. Forkeen, experimenten, rompan las reglas tradicionales del desarrollo de software. La computación adaptativa empieza aquí."

**Cierre:** Preguntas del público. Prepárate para:
- "¿Cómo se conecta el EEG?" → Mostrar brain_server.py con --source muse
- "¿Qué pasa si grito?" → Demostrar con "colapso" o "explosion"
- "¿Puedo usarlo en mi proyecto?" → Sí, es open source, aquí está el repo

---

## Checklist Técnico Pre-Demo

- [ ] Python 3.13 instalado
- [ ] `pip install -r requirements-deploy.txt` (numpy, scipy, Pillow, fastapi, uvicorn, websockets, bleak, sounddevice)
- [ ] Server running: `python deploy_server.py`
- [ ] Unity scene abierta, play mode, conectada a ws://localhost:8765
- [ ] Flutter web: `flutter build web` y sirviendo
- [ ] Micrófono del navegador permitido (Web Speech API)
- [ ] Resolución 1920x1080, 60Hz
- [ ] Sonido: altavoces activados, volumen medio
- [ ] Teléfono en silent / modo avión
- [ ] QR code para repo visible en pantalla de cierre

## Fallbacks

| Fallo | Solución |
|-------|----------|
| Unity no abre | Usar solo Flutter app en navegador (Netlify deploy) |
| BCI no conecta | `--source recorded` para demo sin hardware |
| Micrófono falla | Usar botones predefinidos en Voice Nexus |
| Server no responde | `curl localhost:8765/health` para verificar |
| Fractal muy lento | Reducir `max_iter=64` en URL parámetro |
