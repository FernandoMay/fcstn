import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class StateLog extends StatefulWidget {
  final Stream<String> stateChanges;
  const StateLog({super.key, required this.stateChanges});

  @override
  State<StateLog> createState() => _StateLogState();
}

class _StateLogState extends State<StateLog> {
  final _entries = <_LogEntry>[];
  final _scrollCtrl = ScrollController();
  Timer? _scrollTimer;

  @override
  void initState() {
    super.initState();
    widget.stateChanges.listen((state) {
      if (mounted) {
        setState(() {
          _entries.insert(0, _LogEntry(state, DateTime.now()));
          if (_entries.length > 15) _entries.removeLast();
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 90,
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.outline.withValues(alpha: 0.12)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('STATE LOG',
                style: TextStyle(
                  color: AppColors.onSurface.withValues(alpha: 0.3),
                  fontSize: 8, fontFamily: 'JetBrains Mono', fontWeight: FontWeight.w700, letterSpacing: 1.5,
                ),
              ),
              const SizedBox(width: 6),
              Text('${_entries.length} transitions',
                style: TextStyle(
                  color: AppColors.onSurface.withValues(alpha: 0.15),
                  fontSize: 7, fontFamily: 'JetBrains Mono',
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Expanded(
            child: _entries.isEmpty
              ? Center(child: Text('Esperando señales...',
                  style: TextStyle(color: AppColors.onSurface.withValues(alpha: 0.1), fontSize: 9, fontFamily: 'JetBrains Mono'),
                ))
              : ListView.separated(
                  itemCount: _entries.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 2),
                  itemBuilder: (ctx, i) {
                    final e = _entries[i];
                    final c = _stateColor(e.state);
                    final ts = '${e.time.hour.toString().padLeft(2, '0')}:${e.time.minute.toString().padLeft(2, '0')}:${e.time.second.toString().padLeft(2, '0')}';
                    final isNewest = i == 0;
                    return Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 3),
                      decoration: BoxDecoration(
                        color: c.withValues(alpha: isNewest ? 0.12 : 0.04),
                        borderRadius: BorderRadius.circular(3),
                        border: Border.all(color: c.withValues(alpha: isNewest ? 0.25 : 0.06)),
                      ),
                      child: Row(
                        children: [
                          Text(ts,
                            style: TextStyle(
                              color: isNewest ? c : AppColors.onSurface.withValues(alpha: 0.2),
                              fontSize: 8, fontFamily: 'JetBrains Mono',
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(e.state.toUpperCase(),
                              style: TextStyle(
                                color: c.withValues(alpha: isNewest ? 1.0 : 0.5),
                                fontSize: isNewest ? 11 : 9,
                                fontFamily: 'JetBrains Mono',
                                fontWeight: isNewest ? FontWeight.w900 : FontWeight.w500,
                                letterSpacing: isNewest ? 2 : 1,
                              ),
                            ),
                          ),
                          if (isNewest)
                            Container(
                              width: 5, height: 5,
                              decoration: BoxDecoration(
                                color: c,
                                shape: BoxShape.circle,
                                boxShadow: [BoxShadow(color: c.withValues(alpha: 0.6), blurRadius: 6)],
                              ),
                            ),
                        ],
                      ),
                    );
                  },
                ),
          ),
        ],
      ),
    );
  }

  Color _stateColor(String s) => switch (s) {
    'focused' => AppColors.primaryContainer,
    'stressed' => AppColors.error,
    'fatigued' => const Color(0xFF4488FF),
    'engaged' => AppColors.primary,
    'curious' => AppColors.secondary,
    _ => AppColors.tertiaryContainer,
  };

  @override
  void dispose() {
    _scrollTimer?.cancel();
    _scrollCtrl.dispose();
    super.dispose();
  }
}

class _LogEntry {
  final String state;
  final DateTime time;
  _LogEntry(this.state, this.time);
}
