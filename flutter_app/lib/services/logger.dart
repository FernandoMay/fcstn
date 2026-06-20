import 'dart:developer' as dev;
import 'dart:convert';

class LogEntry {
  final DateTime timestamp;
  final String level;
  final String source;
  final String message;
  final Map<String, dynamic>? data;

  LogEntry({
    required this.timestamp,
    required this.level,
    required this.source,
    required this.message,
    this.data,
  });

  Map<String, dynamic> toJson() => {
    't': timestamp.toIso8601String(),
    'l': level,
    's': source,
    'm': message,
    'd': data ?? {},
  };
}

class Logger {
  final String source;
  final List<LogEntry> _buffer = [];
  static const int _maxEntries = 500;
  static final List<void Function(LogEntry)> _listeners = [];

  Logger(this.source);

  static void addListener(void Function(LogEntry) cb) {
    _listeners.add(cb);
  }

  void _log(String level, String message, [Map<String, dynamic>? data]) {
    final entry = LogEntry(
      timestamp: DateTime.now(),
      level: level,
      source: source,
      message: message,
      data: data,
    );
    _buffer.add(entry);
    if (_buffer.length > _maxEntries) _buffer.removeAt(0);
    for (final cb in _listeners) {
      try { cb(entry); } catch (_) {}
    }
    dev.log('[${source}] $message', name: 'FCSTN');
  }

  void info(String message, [Map<String, dynamic>? data]) => _log('INFO', message, data);
  void warn(String message, [Map<String, dynamic>? data]) => _log('WARN', message, data);
  void error(String message, [Map<String, dynamic>? data]) => _log('ERROR', message, data);
  void debug(String message, [Map<String, dynamic>? data]) => _log('DEBUG', message, data);

  List<LogEntry> recent([int n = 100]) {
    return _buffer.length > n ? _buffer.sublist(_buffer.length - n) : _buffer;
  }
}
