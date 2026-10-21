import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/observation.dart';

void main() {
  test('unknown, zero and trace have distinct summaries', () {
    expect(
      CitizenObservation({
        'kind': 'rain_occurrence',
        'response': 'unknown',
      }).summary,
      'Unknown',
    );
    expect(
      CitizenObservation({
        'kind': 'rainfall_accumulation',
        'amount_state': 'value',
        'value': 0,
        'unit': 'mm',
      }).summary,
      '0 mm',
    );
    expect(
      CitizenObservation({
        'kind': 'rainfall_accumulation',
        'amount_state': 'trace',
        'unit': 'mm',
      }).summary,
      'Trace',
    );
  });
  test('draft snapshot cannot be changed after review', () {
    final payload = <String, dynamic>{
      'observation': {
        'kind': 'flooding',
        'response': 'unknown',
        'surfaces': <String>[],
      },
    };
    final d = ObservationDraft(payload);
    (payload['observation'] as Map)['response'] = 'present';
    expect((d.payload['observation'] as Map)['response'], 'unknown');
    (d.payload['observation'] as Map)['response'] = 'present';
    expect((d.payload['observation'] as Map)['response'], 'unknown');
  });
}
