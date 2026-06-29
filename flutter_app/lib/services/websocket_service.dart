import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart';
import '../models/cognitive_state.dart';
import 'logger.dart';

class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  CognitiveState _currentState = const CognitiveState();
  CognitiveState _targetState = const CognitiveState();
  CognitiveState? _previousState;
  Timer? _interpTimer;
  bool _connected = false;
  String? _error;
  int _reconnectAttempts = 0;
  int _messageCount = 0;
  int _parseErrors = 0;

  final Logger _log = Logger('WS');
  CognitiveState get currentState => _currentState;
  bool get connected => _connected;
  String? get error => _error;
  int get messageCount => _messageCount;
  int get reconnectAttempts => _reconnectAttempts;

  final List<CognitiveState> history = [];
  static const int maxHistory = 120;

  final String _url;
  static const double _interpDuration = 0.05;
  static const double _interpStep = 0.15;

  WebSocketService({String url = 'ws://localhost:8765'}) : _url = url {
    _log.info('Service created', {'url': url});
  }

  Future<void> connect() async {
    _log.info('Connecting', {'url': _url, 'attempt': _reconnectAttempts + 1});
    try {
      _channel = WebSocketChannel.connect(Uri.parse(_url));
      await _channel!.ready;
      _connected = true;
      _error = null;
      _reconnectAttempts = 0;
      _startInterpolation();
      notifyListeners();
      _log.info('Connected', {'url': _url});

      _channel!.stream.listen(
        (data) {
          _messageCount++;
          try {
            final json = jsonDecode(data as String) as Map<String, dynamic>;
            _previousState = _targetState;
            _targetState = CognitiveState.fromJson(json);
            history.add(_targetState);
            if (history.length > maxHistory) history.removeAt(0);
          } catch (e) {
            _parseErrors++;
            _log.warn('Parse error', {'error': '$e', 'raw': data.toString().substring(0, min(100, data.toString().length))});
          }
        },
        onError: (err) {
          _error = 'Connection error: $err';
          _connected = false;
          _log.error('Stream error', {'error': '$err'});
          notifyListeners();
          _scheduleReconnect();
        },
        onDone: () {
          _connected = false;
          _error = 'Connection closed';
          _log.warn('Stream closed', {'messages': _messageCount, 'errors': _parseErrors});
          notifyListeners();
          _scheduleReconnect();
        },
      );
    } catch (e) {
      _error = 'Failed to connect: $e';
      _connected = false;
      _log.error('Connect failed', {'error': '$e', 'url': _url});
      notifyListeners();
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    _reconnectAttempts++;
    final delay = min(30000, 1000 * _reconnectAttempts);
    _log.info('Scheduling reconnect', {'attempt': _reconnectAttempts, 'delay_ms': delay});
    Future.delayed(Duration(milliseconds: delay), () {
      if (!_connected) connect();
    });
  }

  void _startInterpolation() {
    _interpTimer?.cancel();
    _interpTimer = Timer.periodic(
      Duration(milliseconds: (kReleaseMode ? 16 : 50)),
      (_) {
        if (_previousState != null && _targetState != _previousState) {
          final t = _interpStep;
          _currentState = _currentState.lerp(_targetState, t);
          notifyListeners();
        } else {
          _currentState = _currentState.lerp(_targetState, _interpStep);
        }
      },
    );
  }

  void send(String message) {
    if (_connected && _channel != null) {
      _channel!.sink.add(message);
      _log.debug('Sent', {'msg': message.substring(0, min(80, message.length))});
    }
  }

  void sendVoiceCommand(String text) {
    _log.info('Voice command sent', {'text': text});
    send(jsonEncode({'type': 'voice', 'text': text}));
  }

  void setMetrics({
    double? attention,
    double? engagement,
    double? load,
    double? valence,
    String? phase,
  }) {
    final msg = <String, dynamic>{'type': 'set'};
    if (attention != null) msg['attention'] = attention;
    if (engagement != null) msg['engagement'] = engagement;
    if (load != null) msg['load'] = load;
    if (valence != null) msg['valence'] = valence;
    if (phase != null) msg['phase'] = phase;
    _log.info('Set metrics', msg.cast<String, dynamic>());
    send(jsonEncode(msg));
  }

  String get stats {
    return 'msgs=$_messageCount reconnect=$_reconnectAttempts errors=$_parseErrors';
  }

  @override
  void dispose() {
    _interpTimer?.cancel();
    _channel?.sink.close();
    _log.info('Disposed', {'stats': stats});
    super.dispose();
  }
}

int min(int a, int b) => a < b ? a : b;
