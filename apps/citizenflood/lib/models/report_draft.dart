import 'report.dart';
import '../maps/map_selection.dart';

abstract interface class ReviewDraft {
  String get label;
  String get reading;
  List<String> get context;
  SelectedLocation get location;
  DateTime get observedAt;
  String? get note;
  String? get photoPath;
}

class ReportDraft implements ReviewDraft {
  @override
  String get label => category.label;
  @override
  List<String> get context => const [];

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
  @override
  final SelectedLocation location;
  @override
  final DateTime observedAt;
  final double? value;
  final Condition? condition;
  @override
  @override
  final String? note, photoPath;
  @override
  String get reading => category.isNumeric
      ? '$value ${category.unit}'
      : condition?.label ?? 'Choose a condition';
}
