import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/services/depth_preview.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  Map<String, dynamic> reading() => {
    'kind': 'water_reading',
    'reference_kind': 'depth',
    'unit': 'm',
    'value': 0.5,
    'reference_description': 'Road surface',
  };
  test('accepts explicit depth including zero without changing input', () {
    final data = reading();
    expect(DepthPreview.fromObservation(data)?.depthM, 0.5);
    data['value'] = 0;
    expect(DepthPreview.fromObservation(data)?.depthM, 0);
    expect(data['reference_description'], 'Road surface');
  });
  test(
    'rejects stage, qualitative reports, wrong units and invalid values',
    () {
      for (final change in [
        {'reference_kind': 'stage'},
        {'kind': 'flooding'},
        {'unit': 'cm'},
        {'value': -1},
        {'value': double.nan},
        {'value': double.infinity},
        {'value': '0.5'},
        {'value': null},
        {'reference_description': ' '},
      ]) {
        expect(DepthPreview.fromObservation({...reading(), ...change}), isNull);
      }
      expect(DepthPreview.fromObservation(null), isNull);
    },
  );
  test('sends only preview data to native activity', () async {
    MethodCall? received;
    const channel = MethodChannel('citizenflood/depth_preview');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          received = call;
          return null;
        });
    await DepthPreview.fromObservation(
      reading(),
    )!.open(contextLabel: 'Draft depth');
    expect(received!.method, 'open');
    expect(received!.arguments, {
      'depthM': 0.5,
      'reference': 'Road surface',
      'contextLabel': 'Draft depth',
    });
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });
  test(
    'camera water uses a separate launch without changing the reading',
    () async {
      MethodCall? received;
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(DepthPreview.channel, (call) async {
            received = call;
            return null;
          });
      final data = reading();
      await DepthPreview.fromObservation(
        data,
      )!.openCamera(contextLabel: 'Draft depth');
      expect(received!.method, 'openCamera');
      expect(received!.arguments, isNull);
      expect(data['value'], 0.5);
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(DepthPreview.channel, null);
    },
  );
}
