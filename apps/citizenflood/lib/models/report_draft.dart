import 'report.dart';
import '../maps/map_selection.dart';

class ReportDraft {
  const ReportDraft({
    required this.category,
    required this.location,
    required this.observedAt,
    this.value,
    this.condition,
    this.note,
    this.photoPath,
  });
  final ReportCategory category;
  final SelectedLocation location;
  final DateTime observedAt;
  final double? value;
  final Condition? condition;
  final String? note, photoPath;
  String get reading => category.isNumeric
      ? '$value ${category.unit}'
      : condition?.label ?? 'Choose a condition';
}
