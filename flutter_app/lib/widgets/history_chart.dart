import 'package:flutter/material.dart';
import '../models/cognitive_state.dart';
import '../theme/app_colors.dart';

class HistoryChart extends StatelessWidget {
  final List<CognitiveState> history;
  final CognitiveState currentState;
  const HistoryChart({super.key, required this.history, required this.currentState});

  @override
  Widget build(BuildContext context) {
    if (history.isEmpty) {
      return Container(
        height: 100,
        decoration: BoxDecoration(
          color: AppColors.surfaceContainerLow,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: AppColors.outline.withValues(alpha: 0.1)),
        ),
        child: Center(
          child: Text('. . .',
            style: TextStyle(
              color: AppColors.onSurface.withValues(alpha: 0.12),
              fontSize: 20, fontFamily: 'JetBrains Mono', letterSpacing: 4,
            ),
          ),
        ),
      );
    }
    return Container(
      height: 100,
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLow,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.outline.withValues(alpha: 0.15)),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(7),
        child: CustomPaint(
          painter: _ChartPainter(history, currentState),
          size: const Size(double.infinity, 100),
        ),
      ),
    );
  }
}

class _ChartPainter extends CustomPainter {
  final List<CognitiveState> history;
  final CognitiveState current;
  _ChartPainter(this.history, this.current);

  @override
  void paint(Canvas canvas, Size size) {
    final h = history;
    if (h.length < 2) return;
    final count = h.length;
    final w = size.width, hh = size.height;

    for (int i = 0; i < 4; i++) {
      final y = hh * (i + 1) / 5;
      canvas.drawLine(Offset(0, y), Offset(w, y),
        Paint()..color = AppColors.outline.withValues(alpha: 0.04)..strokeWidth = 0.5);
    }

    final lines = [
      ('attention', 0.0, 1.0, AppColors.primary),
      ('load', 0.0, 1.0, AppColors.error),
      ('valence', 0.0, 1.0, const Color(0xFFFFB800)),
      ('fractalDimension', 2.0, 3.0, AppColors.primaryContainer),
    ];

    for (final (field, lo, hi, color) in lines) {
      final path = Path();
      final fillPath = Path();
      bool first = true;
      for (int i = 0; i < count; i++) {
        final val = _getField(h[i], field);
        final norm = ((val - lo) / (hi - lo)).clamp(0.0, 1.0);
        final x = w * i / (count - 1);
        final y = hh * (1.0 - norm);
        if (first) {
          path.moveTo(x, y);
          fillPath.moveTo(x, hh);
          fillPath.lineTo(x, y);
          first = false;
        } else {
          path.lineTo(x, y);
          fillPath.lineTo(x, y);
        }
      }
      if (!first) {
        fillPath.lineTo(w, hh);
        fillPath.close();
        canvas.drawPath(fillPath, Paint()
          ..shader = LinearGradient(
            begin: Alignment.topCenter, end: Alignment.bottomCenter,
            colors: [color.withValues(alpha: 0.15), color.withValues(alpha: 0.0)],
          ).createShader(Rect.fromLTWH(0, 0, w, hh)));
        canvas.drawPath(path, Paint()
          ..color = color.withValues(alpha: 0.55)
          ..style = PaintingStyle.stroke..strokeWidth = 1.5..strokeCap = StrokeCap.round);
      }
    }

    final dv = _getField(current, 'attention');
    final dn = ((dv - 0.0) / 1.0).clamp(0.0, 1.0);
    final dx = w * (count - 1) / (count - 1);
    final dy = hh * (1.0 - dn);
    canvas.drawCircle(Offset(dx, dy), 2.5,
      Paint()..color = AppColors.primary.withValues(alpha: 0.7)..maskFilter = const MaskFilter.blur(BlurStyle.normal, 3));
    canvas.drawCircle(Offset(dx, dy), 1.5, Paint()..color = AppColors.primary);
  }

  double _getField(CognitiveState s, String field) {
    return switch (field) {
      'attention' => s.attention,
      'load' => s.load,
      'valence' => s.valence,
      'fractalDimension' => s.fractalDimension,
      _ => 0.5,
    };
  }

  @override
  bool shouldRepaint(_ChartPainter old) => old.history != history;
}
