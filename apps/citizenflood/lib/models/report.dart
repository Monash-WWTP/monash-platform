import 'package:flutter/material.dart';

/// The kinds of site data a citizen can record.
enum ReportCategory { rainfall, waterLevel, temperature, wastewater }

extension ReportCategoryX on ReportCategory {
  String get wire => switch (this) {
    ReportCategory.rainfall => 'rainfall',
    ReportCategory.waterLevel => 'water_level',
    ReportCategory.temperature => 'temperature',
    ReportCategory.wastewater => 'wastewater',
  };

  String get label => switch (this) {
    ReportCategory.rainfall => 'Rainfall',
    ReportCategory.waterLevel => 'Water level',
    ReportCategory.temperature => 'Temperature',
    ReportCategory.wastewater => 'Wastewater plant',
  };

  IconData get icon => switch (this) {
    ReportCategory.rainfall => Icons.umbrella,
    ReportCategory.waterLevel => Icons.waves,
    ReportCategory.temperature => Icons.thermostat,
    ReportCategory.wastewater => Icons.factory_outlined,
  };

  /// Numeric categories carry a measured value + unit. Wastewater carries a
  /// condition (Normal/Warning/Critical) instead.
  bool get isNumeric => this != ReportCategory.wastewater;

  /// Fixed unit for the numeric categories; empty for wastewater.
  String get unit => switch (this) {
    ReportCategory.rainfall => 'mm',
    ReportCategory.waterLevel => 'm',
    ReportCategory.temperature => '°C',
    ReportCategory.wastewater => '',
  };

  /// Friendly prompt shown above the value input.
  String get readingLabel => switch (this) {
    ReportCategory.rainfall => 'Rainfall (mm)',
    ReportCategory.waterLevel => 'Water level (m)',
    ReportCategory.temperature => 'Temperature (°C)',
    ReportCategory.wastewater => 'Plant condition',
  };

  static ReportCategory fromWire(String value) =>
      ReportCategory.values.firstWhere((c) => c.wire == value);
}

/// Wastewater treatment plant condition.
enum Condition { normal, warning, critical }

extension ConditionX on Condition {
  String get wire => name; // 'normal' | 'warning' | 'critical'
  String get label => switch (this) {
    Condition.normal => 'Normal',
    Condition.warning => 'Warning',
    Condition.critical => 'Critical',
  };
  static Condition fromWire(String value) =>
      Condition.values.firstWhere((c) => c.name == value);
}

enum ModerationStatus { pending, approved, rejected }

extension ModerationStatusX on ModerationStatus {
  String get wire => name;

  static ModerationStatus fromWire(String value) =>
      ModerationStatus.values.firstWhere((s) => s.name == value);
}

class Report {
  final String? id;
  final ReportCategory category;

  /// Measured value for numeric categories (mm / m / °C); null for wastewater.
  final double? readingValue;

  /// Unit string for numeric categories; null for wastewater.
  final String? readingUnit;

  /// Plant condition for wastewater; null for numeric categories.
  final Condition? condition;

  final String? note;
  final double latitude;
  final double longitude;
  final String? photoPath;
  final String? stationCode;
  final double? locationAccuracyM;
  final DateTime? observedAt;
  final ModerationStatus moderationStatus;
  final DateTime? createdAt;

  Report({
    this.id,
    required this.category,
    this.readingValue,
    this.readingUnit,
    this.condition,
    this.note,
    required this.latitude,
    required this.longitude,
    this.photoPath,
    this.stationCode,
    this.locationAccuracyM,
    this.observedAt,
    this.moderationStatus = ModerationStatus.pending,
    this.createdAt,
  });

  /// Human-readable reading, e.g. "12.5 mm" or "Critical".
  String get readingLabel => category.isNumeric
      ? '${_trimNumber(readingValue)} ${readingUnit ?? category.unit}'.trim()
      : (condition?.label ?? '—');

  static String _trimNumber(double? v) {
    if (v == null) return '';
    return v == v.roundToDouble() ? v.toInt().toString() : v.toString();
  }

  /// Columns the client supplies on insert. DB fills id/reporter_id/created_at.
  Map<String, dynamic> toInsertMap() => {
    'category': category.wire,
    'reading_value': readingValue,
    'reading_unit': readingUnit,
    'condition': condition?.wire,
    'note': note,
    'latitude': latitude,
    'longitude': longitude,
    'location_accuracy_m': locationAccuracyM,
    'station_code': stationCode,
    'photo_path': photoPath,
    'observed_at': (observedAt ?? DateTime.now().toUtc()).toIso8601String(),
  };

  factory Report.fromRow(Map<String, dynamic> row) => Report(
    id: row['id'] as String?,
    category: ReportCategoryX.fromWire(row['category'] as String),
    readingValue: (row['reading_value'] as num?)?.toDouble(),
    readingUnit: row['reading_unit'] as String?,
    condition: row['condition'] == null
        ? null
        : ConditionX.fromWire(row['condition'] as String),
    note: row['note'] as String?,
    latitude: (row['latitude'] as num).toDouble(),
    longitude: (row['longitude'] as num).toDouble(),
    locationAccuracyM: (row['location_accuracy_m'] as num?)?.toDouble(),
    stationCode: row['station_code'] as String?,
    photoPath: row['photo_path'] as String?,
    observedAt: row['observed_at'] == null
        ? null
        : DateTime.parse(row['observed_at'] as String),
    moderationStatus: row['moderation_status'] == null
        ? ModerationStatus.approved
        : ModerationStatusX.fromWire(row['moderation_status'] as String),
    createdAt: row['created_at'] == null
        ? null
        : DateTime.parse(row['created_at'] as String),
  );
}
