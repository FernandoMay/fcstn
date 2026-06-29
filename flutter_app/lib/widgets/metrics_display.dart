import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../models/cognitive_state.dart';

class MetricsDisplay extends StatelessWidget {
  final CognitiveState state;
  const MetricsDisplay({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(child: _Gauge(label: 'ATTN', value: state.attention, color: const Color(0xFF00F0FF), sub: 'atencion')),
            Expanded(child: _Gauge(label: 'ENG', value: state.engagement, color: const Color(0xFF00FF88), sub: 'entrega')),
            Expanded(child: _Gauge(label: 'LOAD', value: state.load, color: const Color(0xFFFF4400), sub: 'carga')),
          ],
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            Expanded(child: _Gauge(label: 'VAL', value: state.valence, color: const Color(0xFFFFB800), sub: 'valencia')),
            Expanded(child: _Gauge(label: 'COH', value: state.coherence, color: const Color(0xFF9933FF), sub: 'coherencia')),
            Expanded(child: _Gauge(label: 'DIM', value: (state.fractalDimension - 2.0) / 2.0, color: const Color(0xFFFF0055), sub: state.fractalDimension.toStringAsFixed(2))),
          ],
        ),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                _stateColor(state).withValues(alpha: 0.08),
                Colors.transparent,
              ],
            ),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: _stateColor(state).withValues(alpha: 0.15)),
          ),
          child: Row(
            children: [
              _chip('Φ', state.phase.toUpperCase(), _stateColor(state)),
              const SizedBox(width: 4),
              _chip('D', state.fractalDimension.toStringAsFixed(2), const Color(0xFFFF0055)),
              const SizedBox(width: 4),
              _chip('⚡', state.dominantLabel.toUpperCase(), const Color(0xFF00FF88)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _chip(String prefix, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Text(
        '$prefix $value',
        style: TextStyle(color: color, fontSize: 8, fontFamily: 'monospace', fontWeight: FontWeight.bold, letterSpacing: 0.5),
      ),
    );
  }

  Color _stateColor(CognitiveState s) {
    return switch (s.stateName) {
      'focused' => const Color(0xFFFF0055),
      'stressed' => const Color(0xFFFF4400),
      'fatigued' => const Color(0xFF4488FF),
      'engaged' => const Color(0xFF00F0FF),
      'curious' => const Color(0xFF00FF88),
      _ => const Color(0xFF9933FF),
    };
  }
}

class _Gauge extends StatelessWidget {
  final String label, sub;
  final double value;
  final Color color;
  const _Gauge({required this.label, required this.value, required this.color, this.sub = ''});

  @override
  Widget build(BuildContext context) {
    final clamped = value.clamp(0.0, 1.0);
    return Padding(
      padding: const EdgeInsets.all(2),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 52, height: 52,
            child: CustomPaint(
              painter: _GaugePainter(value: clamped, color: color, animPhase: (DateTime.now().millisecondsSinceEpoch % 2000) / 2000.0),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '${(clamped * 100).round()}',
                      style: TextStyle(
                        color: color,
                        fontSize: 15, fontFamily: 'monospace', fontWeight: FontWeight.w900,
                        shadows: [Shadow(color: color.withValues(alpha: 0.4), blurRadius: 8)],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          Text(
            label,
            style: TextStyle(color: color.withValues(alpha: 0.7), fontSize: 7, fontFamily: 'monospace', fontWeight: FontWeight.bold, letterSpacing: 1),
          ),
          if (sub.isNotEmpty)
            Text(
              sub,
              style: TextStyle(color: color.withValues(alpha: 0.3), fontSize: 6, fontFamily: 'monospace'),
            ),
        ],
      ),
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double value;
  final Color color;
  final double animPhase;
  _GaugePainter({required this.value, required this.color, required this.animPhase});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 4;
    final glow = value * 0.3;

    // Background arc with gradient
    final bgGrad = SweepGradient(
      startAngle: -math.pi / 2,
      endAngle: 3 * math.pi / 2,
      colors: [
        color.withValues(alpha: 0.05),
        color.withValues(alpha: 0.08),
        color.withValues(alpha: 0.03),
      ],
    );
    canvas.drawCircle(center, radius, Paint()
      ..shader = bgGrad.createShader(Rect.fromCircle(center: center, radius: radius + 4))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5);

    // Foreground gradient arc
    final startAngle = -math.pi / 2;
    final sweepAngle = 2 * math.pi * value;

    if (value > 0.01) {
      final fgGrad = SweepGradient(
        startAngle: startAngle,
        endAngle: startAngle + sweepAngle,
        colors: [
          color.withValues(alpha: 0.4),
          color,
          Colors.white.withValues(alpha: 0.8),
        ],
      );
      final fgPaint = Paint()
        ..shader = fgGrad.createShader(Rect.fromCircle(center: center, radius: radius + 4))
        ..style = PaintingStyle.stroke
        ..strokeWidth = 5
        ..strokeCap = StrokeCap.round;
      canvas.drawArc(Rect.fromCircle(center: center, radius: radius), startAngle, sweepAngle, false, fgPaint);

      // Glow dot at tip
      final dotAngle = startAngle + sweepAngle;
      final dotX = center.dx + radius * math.cos(dotAngle);
      final dotY = center.dy + radius * math.sin(dotAngle);

      // Outer glow (pulsing)
      final pulse = math.sin(animPhase * math.pi * 2) * 0.3 + 0.7;
      canvas.drawCircle(Offset(dotX, dotY), 4 + glow * 4, Paint()
        ..color = color.withValues(alpha: glow * pulse)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8));

      // Middle glow
      canvas.drawCircle(Offset(dotX, dotY), 3, Paint()
        ..color = color.withValues(alpha: 0.6 * pulse)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4));

      // Core white dot
      canvas.drawCircle(Offset(dotX, dotY), 1.5, Paint()..color = Colors.white);

      // Inner glow trace
      if (value > 0.2) {
        final traceLen = sweepAngle * 0.3;
        final tracePaint = Paint()
          ..color = color.withValues(alpha: 0.15)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 8
          ..strokeCap = StrokeCap.round
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6);
        canvas.drawArc(Rect.fromCircle(center: center, radius: radius),
            startAngle + (value > 0.5 ? sweepAngle - traceLen : 0), traceLen, false, tracePaint);
      }
    } else {
      // Idle breathing dot
      final idlePulse = math.sin(animPhase * math.pi * 2) * 0.3 + 0.7;
      canvas.drawCircle(center, 2, Paint()
        ..color = color.withValues(alpha: 0.3 * idlePulse)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4));
    }
  }

  @override
  bool shouldRepaint(covariant _GaugePainter old) => old.value != value || old.animPhase != animPhase;
}
