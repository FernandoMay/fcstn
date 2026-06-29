import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../models/cognitive_state.dart';
import '../theme/app_colors.dart';

class MetricsDisplay extends StatelessWidget {
  final CognitiveState state;
  const MetricsDisplay({super.key, required this.state});

  Color _stateColor(CognitiveState s) => switch (s.stateName) {
    'focused' => AppColors.primaryContainer,
    'stressed' => AppColors.error,
    'fatigued' => const Color(0xFF4488FF),
    'engaged' => AppColors.primary,
    'curious' => AppColors.secondary,
    _ => AppColors.tertiaryContainer,
  };

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(child: _Gauge(label: 'ATTN', value: state.attention, color: AppColors.primary)),
            Expanded(child: _Gauge(label: 'ENG', value: state.engagement, color: AppColors.secondary)),
            Expanded(child: _Gauge(label: 'LOAD', value: state.load, color: AppColors.error)),
          ],
        ),
        const SizedBox(height: 6),
        Row(
          children: [
            Expanded(child: _Gauge(label: 'VAL', value: state.valence, color: const Color(0xFFFFB800))),
            Expanded(child: _Gauge(label: 'COH', value: state.coherence, color: const Color(0xFF9933FF))),
            Expanded(child: _Gauge(label: 'DIM', value: (state.fractalDimension - 2.0) / 2.0, color: AppColors.primaryContainer)),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          decoration: BoxDecoration(
            gradient: LinearGradient(colors: [
              _stateColor(state).withValues(alpha: 0.12),
              Colors.transparent,
            ]),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: _stateColor(state).withValues(alpha: 0.2)),
          ),
          child: Row(children: [
            _chip('Φ', state.phase.toUpperCase(), _stateColor(state)),
            const SizedBox(width: 6),
            _chip('D', state.fractalDimension.toStringAsFixed(2), AppColors.primaryContainer),
            const SizedBox(width: 6),
            _chip('⚡', state.dominantLabel.toUpperCase(), AppColors.secondary),
          ]),
        ),
      ],
    );
  }

  Widget _chip(String prefix, String value, Color color) => Expanded(
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Text('$prefix $value',
        textAlign: TextAlign.center,
        style: TextStyle(
          color: color, fontSize: 9, fontFamily: 'JetBrains Mono',
          fontWeight: FontWeight.w700, letterSpacing: 0.5,
        ),
      ),
    ),
  );
}

class _Gauge extends StatelessWidget {
  final String label;
  final double value;
  final Color color;
  const _Gauge({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    final clamped = value.clamp(0.0, 1.0);
    final phase = (DateTime.now().millisecondsSinceEpoch % 2400) / 2400.0;
    return Padding(
      padding: const EdgeInsets.all(3),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 72, height: 72,
            child: CustomPaint(
              painter: _GaugePainter(value: clamped, color: color, phase: phase),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('${(clamped * 100).round()}',
                      style: TextStyle(
                        color: color,
                        fontSize: 20, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.w900,
                        shadows: [Shadow(color: color.withValues(alpha: 0.5), blurRadius: 10)],
                      ),
                    ),
                    Text(label,
                      style: TextStyle(
                        color: color.withValues(alpha: 0.5),
                        fontSize: 7, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.w700, letterSpacing: 1,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double value;
  final Color color;
  final double phase;
  _GaugePainter({required this.value, required this.color, required this.phase});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 6;
    final glow = value * 0.4;

    // Outer glow halo
    canvas.drawCircle(center, radius + 6,
      Paint()
        ..shader = RadialGradient(
          colors: [color.withValues(alpha: glow * 0.2), color.withValues(alpha: 0.0)],
        ).createShader(Rect.fromCircle(center: center, radius: radius + 8))
    );

    // Background arc
    final bgArc = Rect.fromCircle(center: center, radius: radius);
    canvas.drawArc(bgArc, -math.pi / 2, 2 * math.pi, false,
      Paint()
        ..color = AppColors.surfaceContainerHigh
        ..style = PaintingStyle.stroke..strokeWidth = 8..strokeCap = StrokeCap.round);

    // Foreground arc
    if (value > 0.01) {
      final sweep = 2 * math.pi * value;
      canvas.drawArc(bgArc, -math.pi / 2, sweep, false,
        Paint()
          ..shader = SweepGradient(
            startAngle: -math.pi / 2,
            endAngle: -math.pi / 2 + sweep,
            colors: [color.withValues(alpha: 0.3), color, color.withValues(alpha: 0.9)],
          ).createShader(bgArc.inflate(4))
          ..style = PaintingStyle.stroke..strokeWidth = 8..strokeCap = StrokeCap.round);

      // Pulsing dot at tip
      final pulse = math.sin(phase * math.pi * 2) * 0.3 + 0.7;
      final dotAngle = -math.pi / 2 + sweep;
      final dx = center.dx + radius * math.cos(dotAngle);
      final dy = center.dy + radius * math.sin(dotAngle);

      canvas.drawCircle(Offset(dx, dy), 5 + glow * 5,
        Paint()
          ..color = color.withValues(alpha: glow * pulse)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10));
      canvas.drawCircle(Offset(dx, dy), 3,
        Paint()
          ..color = color.withValues(alpha: 0.7 * pulse)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4));
      canvas.drawCircle(Offset(dx, dy), 1.5, Paint()..color = AppColors.onSurface);
    }
  }

  @override
  bool shouldRepaint(_GaugePainter old) => (old.value - value).abs() > 0.01 || (old.phase - phase).abs() > 0.01;
}
