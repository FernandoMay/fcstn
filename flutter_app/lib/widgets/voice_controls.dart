import 'package:flutter/material.dart';
import '../services/websocket_service.dart';
import '../theme/app_colors.dart';

class VoiceControls extends StatefulWidget {
  final WebSocketService service;
  const VoiceControls({super.key, required this.service});
  @override
  State<VoiceControls> createState() => _VoiceControlsState();
}

class _VoiceControlsState extends State<VoiceControls> {
  final _controller = TextEditingController();
  String _lastSent = '';
  final _presets = [
    ('FOCUS', 'foco'),
    ('EXPLODE', 'explosion'),
    ('CALM', 'calma'),
    ('CREATE', 'creativo'),
    ('CHAOS', 'caos'),
    ('REST', 'reposo'),
  ];

  void _sendCommand(String command) {
    widget.service.sendVoiceCommand(command);
    setState(() => _lastSent = command);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLow,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.12)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('VOICE',
                style: TextStyle(
                  color: AppColors.primary.withValues(alpha: 0.6),
                  fontSize: 9, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.w700, letterSpacing: 1,
                ),
              ),
              const Spacer(),
              if (_lastSent.isNotEmpty)
                Text(_lastSent,
                  style: TextStyle(color: AppColors.onSurface.withValues(alpha: 0.25), fontSize: 8, fontFamily: 'JetBrains Mono'),
                ),
            ],
          ),
          const SizedBox(height: 4),
          Wrap(
            spacing: 3, runSpacing: 3,
            children: _presets.map((e) {
              return InkWell(
                onTap: () => _sendCommand(e.$2),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        AppColors.primary.withValues(alpha: 0.08),
                        AppColors.primary.withValues(alpha: 0.02),
                      ],
                    ),
                    border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
                    borderRadius: BorderRadius.circular(3),
                  ),
                  child: Text(e.$1,
                    style: TextStyle(
                      color: AppColors.primary,
                      fontSize: 8, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 24,
                  child: TextField(
                    controller: _controller,
                    style: TextStyle(color: AppColors.onSurface, fontSize: 10, fontFamily: 'JetBrains Mono'),
                    decoration: InputDecoration(
                      hintText: 'command...',
                      hintStyle: TextStyle(color: AppColors.onSurface.withValues(alpha: 0.12), fontSize: 10, fontFamily: 'JetBrains Mono'),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 6, vertical: 0),
                      border: OutlineInputBorder(
                        borderSide: BorderSide(color: AppColors.outline.withValues(alpha: 0.15)),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: AppColors.outline.withValues(alpha: 0.08)),
                      ),
                      filled: true,
                      fillColor: AppColors.surfaceContainer,
                    ),
                    onSubmitted: (v) {
                      if (v.trim().isNotEmpty) { _sendCommand(v.trim()); _controller.clear(); }
                    },
                  ),
                ),
              ),
              const SizedBox(width: 4),
              InkWell(
                onTap: () {
                  if (_controller.text.trim().isNotEmpty) { _sendCommand(_controller.text.trim()); _controller.clear(); }
                },
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(3),
                  ),
                  child: Icon(Icons.bolt, size: 12, color: AppColors.primary),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
