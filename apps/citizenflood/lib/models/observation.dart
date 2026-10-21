import 'dart:convert';
import 'report_draft.dart';
import '../maps/map_selection.dart';

const observationLabels = <String, String>{
  'flooding': 'Flooding',
  'rain_occurrence': 'Rain',
  'water_appearance': 'Water appearance',
  'rainfall_accumulation': 'Gauge rainfall',
  'water_reading': 'Water reading',
  'temperature': 'Temperature',
};

class CitizenObservation {
  CitizenObservation(Map<String, dynamic> input) : _json = jsonEncode(input);
  final String _json;
  Map<String, dynamic> get data => jsonDecode(_json) as Map<String, dynamic>;
  String get kind => data['kind'] as String;
  String get label => observationLabels[kind] ?? 'Unsupported observation';
  String get summary {
    final d = data;
    const responses = {
      'present': 'Observed',
      'not_observed': 'Not observed here',
      'unknown': 'Unknown',
      'features_observed': 'Features observed',
      'trace': 'Trace',
      'missing': 'Missing',
    };
    final state = d['response'] ?? d['amount_state'];
    if (state != null && state != 'value') {
      return responses[state] ?? 'Unspecified';
    }
    return '${d['value']} ${d['unit'] ?? ''}'.trim();
  }

  List<String> get context {
    final d = data;
    return [
      if (d['method'] != null) 'Method: ${d['method']}',
      if (d['movement'] != null) 'Movement: ${d['movement']}',
      if (d['subject'] != null) 'Subject: ${d['subject']}',
      if ((d['features'] as List?)?.isNotEmpty ?? false)
        'Features: ${(d['features'] as List).join(', ')}',
      if ((d['surfaces'] as List?)?.isNotEmpty ?? false)
        'Surface: ${(d['surfaces'] as List).join(', ')}',
      if (d['interval_start'] != null)
        'Collection: ${d['interval_start']} to ${d['interval_end']}',
      if (d['reference_kind'] != null) 'Reference: ${d['reference_kind']}',
      if (d['reference_description'] != null)
        'Surface: ${d['reference_description']}',
      if (d['reference_id'] != null)
        'Gauge: ${d['reference_id']} · revision ${d['reference_revision']}',
      if (d['gauge_type'] != null) 'Gauge type: ${d['gauge_type']}',
      if (d['gauge_id'] != null) 'Gauge/site: ${d['gauge_id']}',
      if (d['instrument'] != null) 'Instrument: ${d['instrument']}',
      if (d['sample_context'] != null) 'Sampling: ${d['sample_context']}',
      if (d['calibration_status'] != null)
        'Reported calibration: ${d['calibration_status']}',
      if (d['calibration_note'] != null) '${d['calibration_note']}',
    ];
  }
}

class ObservationDraft implements ReviewDraft {
  ObservationDraft(Map<String, dynamic> input, {this.photoPath})
    : _json = jsonEncode(input);
  @override
  final String? photoPath;
  @override
  String? get note => payload["note"] as String?;
  @override
  String get label => observation.label;
  @override
  String get reading => observation.summary;
  @override
  List<String> get context => [
    ...observation.context,
    if (payload['photo_source'] != null)
      'Photo source: ${payload['photo_source']}',
    if (payload['previous_observation_id'] != null)
      'Update to: ${payload['previous_observation_id']}',
    if (payload['level_change'] != null) 'Change: ${payload['level_change']}',
  ];
  @override
  DateTime get observedAt => DateTime.parse(payload["observed_at"]);
  @override
  SelectedLocation get location => SelectedLocation(
    latitude: (payload["latitude"] as num).toDouble(),
    longitude: (payload["longitude"] as num).toDouble(),
    source: payload["location_source"] == "current"
        ? LocationSource.current
        : LocationSource.selected,
    accuracyM: (payload["location_accuracy_m"] as num?)?.toDouble(),
  );
  final String _json;
  Map<String, dynamic> get payload => jsonDecode(_json) as Map<String, dynamic>;
  CitizenObservation get observation =>
      CitizenObservation(Map<String, dynamic>.from(payload['observation']));
}
