enum LocationSource { current, selected }

class SelectedLocation {
  const SelectedLocation({
    required this.latitude,
    required this.longitude,
    required this.source,
    this.accuracyM,
  });
  final double latitude, longitude;
  final double? accuracyM;
  final LocationSource source;
  String get label =>
      '${latitude.toStringAsFixed(5)}, ${longitude.toStringAsFixed(5)}';
}

class MapSelection {
  SelectedLocation? location;
  String? observationId;
  void selectObservation(String id) {
    observationId = id;
  }

  void chooseLocation(SelectedLocation value) {
    location = value;
  }

  void clear() {
    location = null;
    observationId = null;
  }
}
