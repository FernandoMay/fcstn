import 'package:flutter/material.dart';
import 'services/websocket_service.dart';
import 'screens/demo_screen.dart';

void main() {
  runApp(const FCSTNApp());
}

String _detectWsUrl() {
  try {
    final uri = Uri.base;
    if (uri.host.isNotEmpty && uri.host != 'localhost' && uri.host != '127.0.0.1') {
      return 'wss://fcstn.onrender.com/ws';
    }
    return 'ws://localhost:8765';
  } catch (_) {
    return 'ws://localhost:8765';
  }
}

class FCSTNApp extends StatelessWidget {
  const FCSTNApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FCSTN',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.cyanAccent,
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: Colors.black,
      ),
      home: DemoScreen(
        service: WebSocketService(url: _detectWsUrl()),
      ),
    );
  }
}
