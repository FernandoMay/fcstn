import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart';
import '../models/cognitive_state.dart';

class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  CognitiveState _currentState = const CognitiveState();
  CognitiveState _targetState = const CognitiveState();
  CognitiveState? _previousState;
  Timer? _interpTimer;
  bool _connected = false;
  String? _error;

  CognitiveState get currentState => _currentState;
  bool get connected => _connected;
  String? get error => _error;

  final String _url;
  static const double _interpDuration = 0.05;
  static const double _interpStep = 0.15;

  WebSocketService({String url = 'ws://localhost:8765'}) : _url = url;

  Future<void> connect() async {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(_url));
      await _channel!.ready;
      _connected = true;
      _error = null;
      _startInterpolation();
      notifyListeners();

      _channel!.stream.listen(
        (data) {
          try {
            final json = jsonDecode(data as String) as Map<String, dynamic>;
            _previousState = _targetState;
            _targetState = CognitiveState.fromJson(json);
          } catch (e) {
            debugPrint('Parse error: $e');
          }
        },
        onError: (err) {
          _error = 'Connection error: $err';
          _connected = false;
          notifyListeners();
        },
        onDone: () {
          _connected = false;
          _error = 'Connection closed';
          notifyListeners();
        },
      );
    } catch (e) {
      _error = 'Failed to connect: $e';
      _connected = false;
      notifyListeners();
    }
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
    }
  }

  void sendVoiceCommand(String text) {
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
    send(jsonEncode(msg));
  }

  @override
  void dispose() {
    _interpTimer?.cancel();
    _channel?.sink.close();
    super.dispose();
  }
}
