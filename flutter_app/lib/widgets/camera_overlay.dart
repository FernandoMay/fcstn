import 'dart:async';
import 'package:flutter/material.dart';
import '../services/camera_service.dart';
import '../models/cognitive_state.dart';
import '../theme/app_colors.dart';

class CameraOverlay extends StatefulWidget {
  final CameraService cameraService;
  final CognitiveState state;
  const CameraOverlay({super.key, required this.cameraService, required this.state});

  @override
  State<CameraOverlay> createState() => _CameraOverlayState();
}

class _CameraOverlayState extends State<CameraOverlay> {
  Timer? _refreshTimer;
  bool _cameraReady = false;
  bool _cameraOn = false;
  final _emotionHistory = <_EmotionEntry>[];
  static const _maxEmotionHistory = 20;

  @override
  void initState() {
    super.initState();
    _autoInit();
  }

  Future<void> _autoInit() async {
    final status = await widget.cameraService.init();
    if (mounted) setState(() => _cameraReady = status == 'ok');
  }

  void _toggleCamera() {
    if (_cameraOn) {
      widget.cameraService.stop();
      _emotionHistory.clear();
      setState(() => _cameraOn = false);
    } else if (_cameraReady) {
      widget.cameraService.start();
      setState(() => _cameraOn = true);
      _refreshTimer?.cancel();
      _refreshTimer = Timer.periodic(const Duration(milliseconds: 400), (_) {
        if (mounted) {
          setState(() {
            final e = widget.cameraService.lastEmotion;
            if (e != null) {
              _emotionHistory.add(_EmotionEntry(e.emotion, e.probability));
              if (_emotionHistory.length > _maxEmotionHistory) _emotionHistory.removeAt(0);
            }
          });
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final emotion = widget.cameraService.lastEmotion;
    final camColor = _emotionColor(emotion?.emotion ?? 'neutral');
    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: camColor.withValues(alpha: _cameraOn ? 0.35 : 0.08)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Container(
                width: 6, height: 6,
                decoration: BoxDecoration(
                  color: _cameraOn ? AppColors.secondary : AppColors.outline,
                  shape: BoxShape.circle,
                  boxShadow: _cameraOn ? [
                    BoxShadow(color: AppColors.secondary.withValues(alpha: 0.5), blurRadius: 6)
                  ] : null,
                ),
              ),
              const SizedBox(width: 6),
              Text('CAM', style: TextStyle(
                color: AppColors.onSurface.withValues(alpha: 0.5),
                fontSize: 9, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.w700, letterSpacing: 1.5,
              )),
              if (_cameraOn && emotion != null) ...[
                const SizedBox(width: 6),
                Text('#${emotion.detections}', style: TextStyle(
                  color: AppColors.onSurface.withValues(alpha: 0.2), fontSize: 8, fontFamily: 'JetBrains Mono',
                )),
              ],
              const Spacer(),
              GestureDetector(
                onTap: _toggleCamera,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: (_cameraOn ? AppColors.error : AppColors.secondary).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    _cameraOn ? 'OFF' : 'ON',
                    style: TextStyle(
                      color: _cameraOn ? AppColors.error : AppColors.secondary,
                      fontSize: 8, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
            ],
          ),
          if (emotion != null && _cameraOn) ...[
            const SizedBox(height: 4),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                  decoration: BoxDecoration(
                    color: camColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(3),
                    border: Border.all(color: camColor.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_emotionIcon(emotion.emotion), style: const TextStyle(fontSize: 10)),
                      const SizedBox(width: 3),
                      Text(emotion.emotion.toUpperCase(),
                        style: TextStyle(color: camColor, fontSize: 10, fontFamily: 'JetBrains Mono',
                          fontWeight: FontWeight.w700, letterSpacing: 1),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(2),
                    child: LinearProgressIndicator(
                      value: emotion.probability,
                      backgroundColor: AppColors.surfaceContainerHigh.withValues(alpha: 0.4),
                      valueColor: AlwaysStoppedAnimation<Color>(camColor.withValues(alpha: 0.6)),
                      minHeight: 4,
                    ),
                  ),
                ),
                const SizedBox(width: 4),
                Text('${(emotion.probability * 100).toStringAsFixed(0)}%',
                  style: TextStyle(color: AppColors.onSurface.withValues(alpha: 0.4), fontSize: 8, fontFamily: 'JetBrains Mono'),
                ),
              ],
            ),
            const SizedBox(height: 4),
            _buildExpressionBars(emotion),
            const SizedBox(height: 4),
            Row(
              children: [
                _faceMetric('EAR', emotion.ear, AppColors.primary),
                const SizedBox(width: 4),
                _faceMetric('SML', emotion.mouthRatio, AppColors.secondary),
                const SizedBox(width: 4),
                _faceMetric('YAW', emotion.noseOffset.abs(), const Color(0xFFFFB800)),
                const SizedBox(width: 4),
                _faceMetric('BROW', emotion.browRaise, AppColors.tertiaryContainer),
              ],
            ),
            const SizedBox(height: 3),
            if (_emotionHistory.length > 1)
              Container(
                height: 8,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: AppColors.outline.withValues(alpha: 0.1)),
                ),
                clipBehavior: Clip.antiAlias,
                child: Row(
                  children: _emotionHistory.map((e) => Expanded(
                    child: Container(color: _emotionColor(e.emotion).withValues(alpha: 0.2 + 0.5 * e.confidence)),
                  )).toList(),
                ),
              ),
          ],
        ],
      ),
    );
  }

  Widget _buildExpressionBars(EmotionResult e) {
    final exps = ['happy', 'sad', 'angry', 'fearful', 'surprised', 'disgusted', 'neutral'];
    return Column(
      children: exps.map((exp) {
        final prob = e.expressions[exp] ?? 0.0;
        final col = _emotionColor(exp);
        if (prob < 0.01) return const SizedBox.shrink();
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 0.5),
          child: Row(
            children: [
              SizedBox(width: 14, child: Text(exp.substring(0, 3).toUpperCase(),
                style: TextStyle(color: col.withValues(alpha: 0.5), fontSize: 6, fontFamily: 'JetBrains Mono'))),
              const SizedBox(width: 3),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(1.5),
                  child: LinearProgressIndicator(
                    value: prob,
                    backgroundColor: AppColors.surfaceContainerHigh.withValues(alpha: 0.3),
                    valueColor: AlwaysStoppedAnimation<Color>(col.withValues(alpha: 0.5)),
                    minHeight: 4,
                  ),
                ),
              ),
              const SizedBox(width: 3),
              Text('${(prob * 100).toStringAsFixed(0)}%',
                style: TextStyle(color: col.withValues(alpha: 0.4), fontSize: 6, fontFamily: 'JetBrains Mono')),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _faceMetric(String label, double value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(3),
          border: Border.all(color: color.withValues(alpha: 0.1)),
        ),
        child: Column(
          children: [
            Text(label, style: TextStyle(color: color.withValues(alpha: 0.5), fontSize: 6, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.bold)),
            const SizedBox(height: 1),
            Text(value.toStringAsFixed(2), style: TextStyle(color: color, fontSize: 8, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.w700)),
          ],
        ),
      ),
    );
  }

  String _emotionIcon(String e) => switch (e) {
    'happy' => '☺', 'sad' => '☹', 'angry' => '😠', 'fearful' => '😨', 'surprised' => '😮', 'disgusted' => '😣', _ => '😐',
  };

  Color _emotionColor(String emotion) => switch (emotion) {
    'happy' => AppColors.secondary, 'sad' => const Color(0xFF4488FF), 'angry' => AppColors.error,
    'fearful' => const Color(0xFFFF00FF), 'surprised' => const Color(0xFFFFCC00),
    'disgusted' => const Color(0xFF88AA00), 'away' => AppColors.outline, _ => AppColors.primary,
  };

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }
}

class _EmotionEntry {
  final String emotion;
  final double confidence;
  _EmotionEntry(this.emotion, this.confidence);
}
