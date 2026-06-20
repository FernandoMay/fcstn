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
            Expanded(child: _Gauge(label: 'ATTN', value: state.attention, color: const Color(0xFF00F0FF))),
            Expanded(child: _Gauge(label: 'ENG', value: state.engagement, color: const Color(0xFF00FF88))),
            Expanded(child: _Gauge(label: 'LOAD', value: state.load, color: const Color(0xFFFF4400))),
          ],
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            Expanded(child: _Gauge(label: 'VAL', value: state.valence, color: const Color(0xFFFFB800))),
            Expanded(child: _Gauge(label: 'COH', value: state.coherence, color: const Color(0xFF9933FF))),
            Expanded(child: _Gauge(label: 'DIM', value: (state.fractalDimension - 2.0) / 2.0, color: const Color(0xFFFF0055))),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.03),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
          ),
          child: Row(
            children: [
              _chip('Φ', state.phase.toUpperCase(), const Color(0xFF00F0FF)),
              const SizedBox(width: 4),
              _chip('D', state.fractalDimension.toStringAsFixed(2), const Color(0xFFFF0055)),
              const SizedBox(width: 4),
              _chip('DOM', state.dominantLabel.toUpperCase(), const Color(0xFF00FF88)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _chip(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Text(
        '$label $value',
        style: TextStyle(color: color, fontSize: 8, fontFamily: 'monospace', fontWeight: FontWeight.bold),
      ),
    );
  }
}

class _Gauge extends StatelessWidget {
  final String label;
  final double value;
  final Color color;
  const _Gauge({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    final clamped = value.clamp(0.0, 1.0);
    return Padding(
      padding: const EdgeInsets.all(2),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 48, height: 48,
            child: CustomPaint(
              painter: _GaugePainter(value: clamped, color: color),
              child: Center(
                child: Text(
                  '${(clamped * 100).round()}',
                  style: TextStyle(
                    color: color,
                    fontSize: 14, fontFamily: 'monospace', fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ),
          ),
          Text(
            label,
            style: TextStyle(color: color.withValues(alpha: 0.6), fontSize: 7, fontFamily: 'monospace', fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double value;
  final Color color;
  _GaugePainter({required this.value, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 4;

    final bgPaint = Paint()
      ..color = color.withValues(alpha: 0.1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius, bgPaint);

    final fgPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round;

    final startAngle = -math.pi / 2;
    final sweepAngle = 2 * math.pi * value;
    canvas.drawArc(Rect.fromCircle(center: center, radius: radius), startAngle, sweepAngle, false, fgPaint);

    // Glow dot
    if (value > 0.01) {
      final dotAngle = startAngle + sweepAngle;
      final dotX = center.dx + radius * math.cos(dotAngle);
      final dotY = center.dy + radius * math.sin(dotAngle);
      final dotPaint = Paint()
        ..color = color
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6);
      canvas.drawCircle(Offset(dotX, dotY), 3, dotPaint);
      canvas.drawCircle(Offset(dotX, dotY), 1.5, Paint()..color = Colors.white);
    }
  }

  @override
  bool shouldRepaint(covariant _GaugePainter old) => old.value != value;
}
