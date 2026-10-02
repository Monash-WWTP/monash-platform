import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';

void main() {
  test('category maps to and from its wire value', () {
    expect(ReportCategory.waterLevel.wire, 'water_level');
    expect(ReportCategoryX.fromWire('water_level'), ReportCategory.waterLevel);
    expect(ReportCategoryX.fromWire('wastewater'), ReportCategory.wastewater);
  });

  test('numeric categories declare units; wastewater does not', () {
    expect(ReportCategory.rainfall.isNumeric, isTrue);
    expect(ReportCategory.rainfall.unit, 'mm');
    expect(ReportCategory.temperature.unit, '°C');
    expect(ReportCategory.wastewater.isNumeric, isFalse);
    expect(ReportCategory.wastewater.unit, '');
  });

  test('toInsertMap for a numeric reading', () {
    final report = Report(
      category: ReportCategory.rainfall,
      readingValue: 12.5,
      readingUnit: 'mm',
      note: 'heavy downpour',
      latitude: -37.91,
      longitude: 145.13,
      locationAccuracyM: 8.5,
      observedAt: DateTime.utc(2026, 6, 5, 10, 30),
      photoPath: 'abc.jpg',
    );

    final map = report.toInsertMap();

    expect(map['category'], 'rainfall');
    expect(map['reading_value'], 12.5);
    expect(map['reading_unit'], 'mm');
    expect(map['condition'], isNull);
    expect(map['note'], 'heavy downpour');
    expect(map['latitude'], -37.91);
    expect(map['location_accuracy_m'], 8.5);
    expect(map['observed_at'], '2026-06-05T10:30:00.000Z');
    expect(map['photo_path'], 'abc.jpg');
    // id / reporter_id / created_at are set by the database, not the client.
    expect(map.containsKey('id'), isFalse);
  });

  test('toInsertMap for a wastewater condition', () {
    final report = Report(
      category: ReportCategory.wastewater,
      condition: Condition.critical,
      latitude: 1.0,
      longitude: 2.0,
    );

    final map = report.toInsertMap();

    expect(map['category'], 'wastewater');
    expect(map['condition'], 'critical');
    expect(map['reading_value'], isNull);
    expect(map['reading_unit'], isNull);
  });

  test('readingLabel formats value and condition', () {
    final rain = Report(
      category: ReportCategory.rainfall,
      readingValue: 12.0,
      readingUnit: 'mm',
      latitude: 0,
      longitude: 0,
    );
    expect(rain.readingLabel, '12 mm');

    final plant = Report(
      category: ReportCategory.wastewater,
      condition: Condition.warning,
      latitude: 0,
      longitude: 0,
    );
    expect(plant.readingLabel, 'Warning');
  });

  test('fromRow parses a numeric row including timestamp', () {
    final report = Report.fromRow({
      'id': 'uuid-1',
      'category': 'temperature',
      'reading_value': 29.4,
      'reading_unit': '°C',
      'condition': null,
      'note': null,
      'latitude': 1.0,
      'longitude': 2.0,
      'location_accuracy_m': 4.0,
      'station_code': null,
      'photo_path': null,
      'observed_at': '2026-06-05T10:30:00.000Z',
      'created_at': '2026-06-05T10:33:00.000Z',
    });

    expect(report.category, ReportCategory.temperature);
    expect(report.readingValue, 29.4);
    expect(report.readingUnit, '°C');
    expect(report.condition, isNull);
    expect(report.note, isNull);
    expect(report.locationAccuracyM, 4.0);
    expect(report.observedAt!.toUtc().minute, 30);
    expect(report.moderationStatus, ModerationStatus.approved);
    expect(report.createdAt!.toUtc().hour, 10);
  });

  test('fromRow parses a wastewater condition row', () {
    final report = Report.fromRow({
      'id': 'uuid-2',
      'category': 'wastewater',
      'reading_value': null,
      'reading_unit': null,
      'condition': 'normal',
      'latitude': 1.0,
      'longitude': 2.0,
      'created_at': '2026-06-05T10:33:00.000Z',
    });

    expect(report.category, ReportCategory.wastewater);
    expect(report.condition, Condition.normal);
    expect(report.readingValue, isNull);
  });
}
