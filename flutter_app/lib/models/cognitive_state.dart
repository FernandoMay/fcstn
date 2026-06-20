import 'dart:math';

class CognitiveState {
  final double attention;
  final double engagement;
  final double load;
  final double valence;
  final double coherence;
  final double fractalDimension;
  final String narrative;
  final String phase;
  final String stateName;

  const CognitiveState({
    this.attention = 0.5,
    this.engagement = 0.5,
    this.load = 0.3,
    this.valence = 0.5,
    this.coherence = 0.5,
    this.fractalDimension = 2.5,
    this.narrative = '',
    this.phase = 'resting',
    this.stateName = 'resting',
  });

  factory CognitiveState.fromJson(Map<String, dynamic> json) {
    final data = json['data'] as Map<String, dynamic>? ?? json;
    return CognitiveState(
      attention: (data['attention'] as num?)?.toDouble() ?? 0.5,
      engagement: (data['engagement'] as num?)?.toDouble() ?? 0.5,
      load: (data['load'] as num?)?.toDouble() ?? 0.3,
      valence: (data['valence'] as num?)?.toDouble() ?? 0.5,
      coherence: (data['coherence'] as num?)?.toDouble() ?? 0.5,
      fractalDimension: (data['fractal_dimension'] as num?)?.toDouble() ?? 2.5,
      narrative: data['narrative'] as String? ?? '',
      phase: data['phase'] as String? ?? data['state_name'] as String? ?? 'resting',
      stateName: data['state_name'] as String? ?? data['phase'] as String? ?? 'resting',
    );
  }

  Map<String, dynamic> toJson() => {
    'attention': attention,
    'engagement': engagement,
    'load': load,
    'valence': valence,
    'coherence': coherence,
    'fractal_dimension': fractalDimension,
    'narrative': narrative,
    'phase': phase,
    'state_name': stateName,
  };

  CognitiveState copyWith({
    double? attention,
    double? engagement,
    double? load,
    double? valence,
    double? coherence,
    double? fractalDimension,
    String? narrative,
    String? phase,
    String? stateName,
  }) {
    return CognitiveState(
      attention: attention ?? this.attention,
      engagement: engagement ?? this.engagement,
      load: load ?? this.load,
      valence: valence ?? this.valence,
      coherence: coherence ?? this.coherence,
      fractalDimension: fractalDimension ?? this.fractalDimension,
      narrative: narrative ?? this.narrative,
      phase: phase ?? this.phase,
      stateName: stateName ?? this.stateName,
    );
  }

  double get dominantMetric {
    return [attention, engagement, load, valence, coherence].reduce(max);
  }

  String get dominantLabel {
    final map = {
      'attention': attention,
      'engagement': engagement,
      'load': load,
      'valence': valence,
      'coherence': coherence,
    };
    return map.entries.reduce((a, b) => a.value > b.value ? a : b).key;
  }

  double lerpMetric(double a, double b, double t) => a + (b - a) * t;

  CognitiveState lerp(CognitiveState target, double t) {
    return CognitiveState(
      attention: lerpMetric(attention, target.attention, t),
      engagement: lerpMetric(engagement, target.engagement, t),
      load: lerpMetric(load, target.load, t),
      valence: lerpMetric(valence, target.valence, t),
      coherence: lerpMetric(coherence, target.coherence, t),
      fractalDimension: lerpMetric(fractalDimension, target.fractalDimension, t),
      narrative: narrative,
      phase: phase,
      stateName: stateName,
    );
  }
}
