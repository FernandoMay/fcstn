import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/websocket_service.dart';
import '../services/camera_service.dart';
import '../widgets/fractal_viewer.dart';
import '../widgets/metrics_display.dart';
import '../widgets/voice_controls.dart';
import '../widgets/camera_overlay.dart';
import '../widgets/history_chart.dart';
import '../widgets/state_log.dart';
import '../widgets/scanline_overlay.dart';
import '../theme/app_colors.dart';
import '../models/cognitive_state.dart';

class DemoScreen extends StatefulWidget {
  final WebSocketService service;
  const DemoScreen({super.key, required this.service});
  @override
  State<DemoScreen> createState() => _DemoScreenState();
}

class _DemoScreenState extends State<DemoScreen> {
  FractalMode _fractalMode = FractalMode.auto;
  late final CameraService _cameraService;
  String _lastStateName = '';
  final _stateChangeController = StreamController<String>.broadcast();
  Stream<String> get stateChanges => _stateChangeController.stream;

  @override
  void initState() {
    super.initState();
    _cameraService = CameraService(widget.service);
    widget.service.addListener(_onStateChanged);
    widget.service.connect();
    _lastStateName = widget.service.currentState.stateName;
  }

  void _onStateChanged() {
    if (!mounted) return;
    final newState = widget.service.currentState.stateName;
    if (newState != _lastStateName && _lastStateName.isNotEmpty) {
      _stateChangeController.add(newState);
    }
    _lastStateName = newState;
    setState(() {});
  }

  @override
  void dispose() {
    widget.service.removeListener(_onStateChanged);
    _cameraService.dispose();
    _stateChangeController.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.service.currentState;
    final size = MediaQuery.of(context).size;
    final isLandscape = size.width > size.height;
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        systemNavigationBarColor: Colors.black,
      ),
      child: Scaffold(
        body: Stack(
          children: [
            SafeArea(
              child: isLandscape ? _buildLandscape(state) : _buildPortrait(state),
            ),
            const ScanlineOverlay(),
          ],
        ),
      ),
    );
  }

  Widget _buildLandscape(CognitiveState state) {
    return Row(
      children: [
        SizedBox(width: 300, child: _buildSidebar(state)),
        Expanded(child: _buildCenter(state)),
      ],
    );
  }

  Widget _buildPortrait(CognitiveState state) {
    return Column(
      children: [
        Expanded(flex: 3, child: _buildCenter(state)),
        Expanded(flex: 2, child: _buildSidebar(state)),
      ],
    );
  }

  Widget _buildCenter(CognitiveState state) {
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
          _buildNarrative(state),
          const SizedBox(height: 6),
          StateLog(stateChanges: stateChanges),
        ],
      ),
    );
  }

  Widget _buildNarrative(CognitiveState state) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [
          _stateColor(state).withValues(alpha: 0.06),
          AppColors.surfaceContainerLow,
        ]),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _stateColor(state).withValues(alpha: 0.15)),
      ),
      child: Text(
        state.narrative.isNotEmpty ? state.narrative : 'Sintonizando red fractal...',
        style: TextStyle(
          color: AppColors.onSurface.withValues(alpha: 0.5),
          fontSize: 11, fontFamily: 'Inter', fontStyle: FontStyle.italic,
        ),
      ),
    );
  }

  Widget _buildSidebar(CognitiveState state) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        border: Border(
          right: BorderSide(color: AppColors.primary.withValues(alpha: 0.1)),
        ),
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(state),
            const SizedBox(height: 10),
            MetricsDisplay(state: state),
            const SizedBox(height: 8),
            HistoryChart(history: widget.service.history, currentState: state),
            const SizedBox(height: 8),
            CameraOverlay(cameraService: _cameraService, state: state),
            const SizedBox(height: 8),
            VoiceControls(service: widget.service),
            const SizedBox(height: 8),
            _buildFooter(state),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(CognitiveState state) {
    final connected = widget.service.connected;
    final statusColor = connected ? AppColors.secondary : AppColors.error;
    final stateColor = _stateColor(state);
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [
          stateColor.withValues(alpha: 0.12),
          stateColor.withValues(alpha: 0.02),
        ]),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: stateColor.withValues(alpha: 0.2)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 10, height: 10,
                decoration: BoxDecoration(
                  color: statusColor,
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: statusColor.withValues(alpha: 0.6), blurRadius: 10)],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  state.stateName.toUpperCase(),
                  style: TextStyle(
                    color: stateColor,
                    fontSize: 18, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.w900,
                    letterSpacing: 3,
                    shadows: [Shadow(color: stateColor.withValues(alpha: 0.4), blurRadius: 12)],
                  ),
                ),
              ),
              Text(
                connected ? '●' : '○',
                style: TextStyle(color: statusColor, fontSize: 12, fontFamily: 'JetBrains Mono'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFooter(CognitiveState state) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLow,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        'D=${state.fractalDimension.toStringAsFixed(2)} | ${widget.service.stats}',
        style: TextStyle(color: AppColors.onSurface.withValues(alpha: 0.35), fontSize: 8, fontFamily: 'JetBrains Mono'),
      ),
    );
  }

  Color _stateColor(CognitiveState state) => switch (state.stateName) {
    'focused' => AppColors.primaryContainer,
    'stressed' => AppColors.error,
    'fatigued' => const Color(0xFF4488FF),
    'engaged' => AppColors.primary,
    'curious' => AppColors.secondary,
    _ => AppColors.tertiaryContainer,
  };
}
