import 'package:flutter/material.dart';
import '../services/websocket_service.dart';

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
        border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.15)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('VOICE', style: TextStyle(color: Colors.cyanAccent.withValues(alpha: 0.7), fontSize: 9, fontFamily: 'monospace', fontWeight: FontWeight.w700, letterSpacing: 1)),
              const Spacer(),
              if (_lastSent.isNotEmpty)
                Text(_lastSent, style: const TextStyle(color: Colors.white24, fontSize: 8, fontFamily: 'monospace')),
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
                        Colors.cyanAccent.withValues(alpha: 0.08),
                        Colors.cyanAccent.withValues(alpha: 0.02),
                      ],
                    ),
                    border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.2)),
                    borderRadius: BorderRadius.circular(3),
                  ),
                  child: Text(e.$1, style: const TextStyle(color: Colors.cyanAccent, fontSize: 8, fontFamily: 'monospace', fontWeight: FontWeight.bold)),
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
                    style: const TextStyle(color: Colors.white, fontSize: 10, fontFamily: 'monospace'),
                    decoration: InputDecoration(
                      hintText: 'command...',
                      hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.15), fontSize: 10, fontFamily: 'monospace'),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 6, vertical: 0),
                      border: OutlineInputBorder(borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1))),
                      enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.05))),
                      filled: true,
                      fillColor: Colors.white.withValues(alpha: 0.03),
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
                    color: Colors.cyanAccent.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(3),
                  ),
                  child: const Icon(Icons.bolt, size: 12, color: Colors.cyanAccent),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
