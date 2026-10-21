import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/maps/citizen_map.dart';
import 'package:citizenflood/models/report.dart';

void main() {
  test('public approximate markers differ from precise owner markers', () {
    expect(
      CitizenMap.markerImageKey(ReportCategory.rainfall, true),
      isNot(CitizenMap.markerImageKey(ReportCategory.rainfall, false)),
    );
  });
}
