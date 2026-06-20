import 'dart:math';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import '../models/cognitive_state.dart';

class FractalPainter extends CustomPainter {
  final CognitiveState state;
  final double time;

  FractalPainter({required this.state, required this.time});

  @override
  void paint(Canvas canvas, Size size) {
    final dim = state.fractalDimension.clamp(1.5, 3.5);
    final load = state.load;
    final attention = state.attention;
    final valence = state.valence;
    final engagement = state.engagement;
    final coherence = state.coherence;

    final center = Offset(size.width / 2, size.height / 2);
    final maxRadius = min(size.width, size.height) / 2.2;
    final layers = (5 + (dim * 3).round()).clamp(6, 18);

    final hueBase = (valence * 0.4 + time * 0.02) % 1.0;

    for (int layer = 0; layer < layers; layer++) {
      final layerFrac = layer / layers;
      final radius = maxRadius * (0.2 + 0.8 * (1 - layerFrac * 0.5));
      final branches = (3 + layer * 3 + (dim * 2).round()).clamp(4, 40);
      final branchAngle = 2 * pi / branches;
      final rotOffset = time * (0.3 + layer * 0.05) + layer * 0.5;
      final amp = 0.03 * (1 + load * 0.5) * radius;
      final freq = 2.0 + engagement * 3 + layerFrac * 2;

      for (int b = 0; b < branches; b++) {
        final baseAngle = b * branchAngle + rotOffset;
        final x1 = center.dx + cos(baseAngle) * radius;
        final y1 = center.dy + sin(baseAngle) * radius;

        final wobble = sin(time * freq + b * 1.5 + layer) * amp;
        final wobbleAngle = baseAngle + wobble / radius;
        final x2 = center.dx + cos(wobbleAngle) * radius * 0.85;
        final y2 = center.dy + sin(wobbleAngle) * radius * 0.85;

        final hue = (hueBase + layerFrac * 0.3 + b * 0.05) % 1.0;
        final saturation = 0.5 + engagement * 0.5;
        final lightness = 0.3 + load * 0.4 + layerFrac * 0.15;
        final color = HSLColor.fromAHSL(1.0, hue * 360, saturation, lightness).toColor();

        final strokeW = (1.0 + attention * 2.5 - layerFrac * 0.5).clamp(0.5, 4.0);

        final paint = Paint()
          ..color = color.withValues(alpha: 0.6 + coherence * 0.4)
          ..strokeWidth = strokeW
          ..style = PaintingStyle.stroke
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 1.5);

        canvas.drawLine(center, Offset(x1, y1), paint);

        if (layer < layers - 1) {
          final childRadius = radius * (1 / dim).clamp(0.3, 0.75);
          for (int c = 0; c < 3; c++) {
            final childAngle = wobbleAngle + (c - 1) * 0.4;
            final cx = x1 + cos(childAngle) * childRadius * 0.6;
            final cy = y1 + sin(childAngle) * childRadius * 0.6;
            canvas.drawLine(
              Offset(x1, y1),
              Offset(cx, cy),
              paint..color = color.withValues(alpha: 0.3 + coherence * 0.3),
            );
          }
        }
      }
    }

    if (load > 0.65) {
      final glitchCount = (load * 8).round();
      final glitchPaint = Paint()
        ..color = Colors.cyan.withValues(alpha: 0.08 * load)
        ..style = PaintingStyle.fill;
      for (int i = 0; i < glitchCount; i++) {
        final rx = Random(i * 100 + (time * 10).toInt()).nextDouble() * size.width;
        final ry = Random(i * 200 + (time * 10).toInt()).nextDouble() * size.height;
        final rw = Random(i * 300).nextDouble() * size.width * 0.3;
        final rh = 2.0 + Random(i * 400).nextDouble() * 8;
        canvas.drawRect(Rect.fromLTWH(rx, ry, rw, rh), glitchPaint);
      }
    }

    final glowPaint = Paint()
      ..shader = RadialGradient(
        center: Alignment.center,
        radius: 0.8,
        colors: [
          HSLColor.fromAHSL(0.15, hueBase * 360, 0.8, 0.6).toColor(),
          Colors.transparent,
        ],
      ).createShader(Rect.fromCircle(center: center, radius: maxRadius));
    canvas.drawCircle(center, maxRadius, glowPaint);

    final outerPaint = Paint()
      ..color = HSLColor.fromAHSL(
        0.3 + coherence * 0.3,
        hueBase * 360,
        0.7,
        0.5,
      ).toColor()
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;
    canvas.drawCircle(center, maxRadius * 0.9, outerPaint);
  }

  @override
  bool shouldRepaint(FractalPainter oldDelegate) =>
      oldDelegate.state != state || oldDelegate.time != time;
}
