import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/cognitive_state.dart';

enum FractalMode { auto, mandelbrot, terrain, julia }

class FractalViewer extends StatefulWidget {
  final CognitiveState state;
  final String baseUrl;
  final FractalMode mode;
  final ValueChanged<FractalMode> onModeChanged;

  const FractalViewer({
    super.key,
    required this.state,
    this.baseUrl = '',
    this.mode = FractalMode.auto,
    required this.onModeChanged,
  });

  @override
  State<FractalViewer> createState() => _FractalViewerState();
}

class _FractalViewerState extends State<FractalViewer> {
  Uint8List? _currentImage;
  Uint8List? _nextImage;
  double _crossfade = 1.0;
  Timer? _refreshTimer;
  int _frameCount = 0;
  String _lastUrl = '';

  String get _apiBase => widget.baseUrl.isEmpty ? '' : widget.baseUrl;

  String _buildUrl() {
    final s = widget.state;
    final base = _apiBase;
    switch (widget.mode) {
      case FractalMode.auto:
        return '$base/api/fractal/state?width=960&height=540';
      case FractalMode.mandelbrot:
        final zoom = 1.0 + s.attention * 3.0 + s.engagement * 2.0;
        final cx = -0.5 + (s.valence - 0.5) * 0.3;
        final cy = 0.0 + (s.attention - 0.5) * 0.2;
        return '$base/api/fractal?mode=mandelbrot&palette=${_paletteFor(s)}&zoom=$zoom&cx=$cx&cy=$cy&width=960&height=540';
      case FractalMode.terrain:
        final zoom = 1.0 + s.attention * 2.0;
        return '$base/api/fractal?mode=terrain&palette=${_paletteFor(s)}&zoom=$zoom&width=960&height=540';
      case FractalMode.julia:
        final cx = -0.5 + (s.valence - 0.5) * 1.5;
        final cy = 0.0 + (s.engagement - 0.5) * 1.0;
        return '$base/api/fractal?mode=julia&palette=${_paletteFor(s)}&julia_cx=$cx&julia_cy=$cy&width=960&height=540';
    }
  }

  String _paletteFor(CognitiveState s) {
    switch (s.stateName) {
      case 'focused': return 'cyberpunk';
      case 'stressed': return 'fire';
      case 'fatigued': return 'oceanic';
      case 'engaged': return 'neon';
      case 'curious': return 'aurora';
      case 'resting': return 'magnetic';
      default: return 'cyberpunk';
    }
  }

  @override
  void initState() {
    super.initState();
    _fetchImage();
    _refreshTimer = Timer.periodic(const Duration(milliseconds: 500), (_) {
      _frameCount++;
      final url = _buildUrl();
      if (url != _lastUrl || _frameCount % 4 == 0) {
        _lastUrl = url;
        _fetchImage();
      }
    });
  }

  Future<void> _fetchImage() async {
    try {
      final url = _buildUrl();
      final uri = Uri.parse(url);
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _nextImage = response.bodyBytes;
            _crossfade = 0.0;
          });
        }
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_nextImage != null && _crossfade < 1.0) {
      _crossfade = (_crossfade + 0.05).clamp(0.0, 1.0);
      if (_crossfade >= 1.0) {
        _currentImage = _nextImage;
        _nextImage = null;
      }
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Stack(
        fit: StackFit.expand,
        children: [
          Container(color: const Color(0xFF0a0a1a)),
          if (_currentImage != null)
            Image.memory(_currentImage!, fit: BoxFit.cover, gaplessPlayback: true),
          if (_nextImage != null)
            Opacity(
              opacity: _crossfade,
              child: Image.memory(_nextImage!, fit: BoxFit.cover, gaplessPlayback: true),
            ),
          if (_currentImage == null && _nextImage == null)
            const Center(child: CircularProgressIndicator(color: Colors.cyanAccent)),
          Positioned(
            top: 8, left: 8,
            child: _ModeSelector(current: widget.mode, onChanged: widget.onModeChanged),
          ),
          Positioned(
            bottom: 8, right: 8,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.black54, borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                widget.mode.name.toUpperCase(),
                style: const TextStyle(color: Colors.cyanAccent, fontSize: 9, fontFamily: 'monospace'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ModeSelector extends StatelessWidget {
  final FractalMode current;
  final ValueChanged<FractalMode> onChanged;
  const _ModeSelector({required this.current, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.black54, borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: FractalMode.values.map((m) {
          final active = m == current;
          return GestureDetector(
            onTap: () => onChanged(m),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
              decoration: BoxDecoration(
                color: active ? Colors.cyanAccent.withValues(alpha: 0.2) : null,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                m.name[0].toUpperCase() + m.name.substring(1),
                style: TextStyle(
                  color: active ? Colors.cyanAccent : Colors.white38,
                  fontSize: 9, fontFamily: 'monospace',
                  fontWeight: active ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
