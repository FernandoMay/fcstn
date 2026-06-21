import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/websocket_service.dart';
import '../widgets/fractal_viewer.dart';
import '../widgets/metrics_display.dart';
import '../widgets/voice_controls.dart';
import '../models/cognitive_state.dart';

class DemoScreen extends StatefulWidget {
  final WebSocketService service;
  const DemoScreen({super.key, required this.service});
  @override
  State<DemoScreen> createState() => _DemoScreenState();
}

class _DemoScreenState extends State<DemoScreen> {
  FractalMode _fractalMode = FractalMode.auto;

  @override
  void initState() {
    super.initState();
    widget.service.addListener(_onStateChanged);
    widget.service.connect();
  }

  void _onStateChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    widget.service.removeListener(_onStateChanged);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.service.currentState;
    final size = MediaQuery.of(context).size;
    final isLandscape = size.width > size.height;
    final cs = Theme.of(context).colorScheme;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        systemNavigationBarColor: cs.surface.toARGB32(),
      ),
      child: Scaffold(
        body: SafeArea(
          child: isLandscape ? _buildLandscape(state) : _buildPortrait(state),
        ),
      ),
    );
  }

  Widget _buildLandscape(CognitiveState state) {
    return Row(
      children: [
        SizedBox(width: 220, child: _buildSidebar(state)),
        Expanded(child: _buildCenter(state)),
      ],
    );
  }

  Widget _buildPortrait(CognitiveState state) {
    return Column(
      children: [
        Expanded(child: _buildCenter(state)),
        SizedBox(height: 200, child: _buildSidebar(state)),
      ],
    );
  }

  Widget _buildCenter(CognitiveState state) {
    final cs = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.all(8),
      child: Column(
        children: [
          Expanded(
            child: FractalViewer(
              state: state,
              baseUrl: '',
              mode: _fractalMode,
              onModeChanged: (m) => setState(() => _fractalMode = m),
            ),
          ),
          const SizedBox(height: 6),
          _buildNarrative(state, cs),
        ],
      ),
    );
  }

  Widget _buildNarrative(CognitiveState state, ColorScheme cs) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: cs.onSurface.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: cs.outline.withValues(alpha: 0.2)),
      ),
      child: Text(
        state.narrative.isNotEmpty ? state.narrative : 'Sintonizando red fractal...',
        style: TextStyle(
          color: cs.onSurface.withValues(alpha: 0.5),
          fontSize: 11, fontFamily: 'monospace', fontStyle: FontStyle.italic,
        ),
      ),
    );
  }

  Widget _buildSidebar(CognitiveState state) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: cs.surfaceContainerLow,
        border: Border(
          right: BorderSide(color: cs.primary.withValues(alpha: 0.1)),
        ),
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(state, cs),
            const SizedBox(height: 8),
            MetricsDisplay(state: state),
            const SizedBox(height: 8),
            VoiceControls(service: widget.service),
            const SizedBox(height: 8),
            _buildFooter(state, cs),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(CognitiveState state, ColorScheme cs) {
    final connected = widget.service.connected;
    final statusColor = connected ? cs.secondary : cs.error;
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _stateColor(state).withValues(alpha: 0.15),
            Colors.transparent,
          ],
        ),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _stateColor(state).withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          Container(
            width: 8, height: 8,
            decoration: BoxDecoration(
              color: statusColor,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: statusColor.withValues(alpha: 0.5),
                  blurRadius: 8,
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              state.stateName.toUpperCase(),
              style: TextStyle(
                color: _stateColor(state),
                fontSize: 13, fontFamily: 'monospace', fontWeight: FontWeight.w700,
                letterSpacing: 2,
              ),
            ),
          ),
          Text(
            connected ? '●' : '○',
            style: TextStyle(
              color: statusColor,
              fontSize: 10, fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFooter(CognitiveState state, ColorScheme cs) {
    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: cs.onSurface.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        'D=${state.fractalDimension.toStringAsFixed(2)} | ${widget.service.stats}',
        style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 8, fontFamily: 'monospace'),
      ),
    );
  }

  Color _stateColor(CognitiveState state) {
    switch (state.stateName) {
      case 'focused': return const Color(0xFFFF0055);
      case 'stressed': return const Color(0xFFFF4400);
      case 'fatigued': return const Color(0xFF4488FF);
      case 'engaged': return const Color(0xFF00F0FF);
      case 'curious': return const Color(0xFF00FF88);
      default: return const Color(0xFF9933FF);
    }
  }
}
