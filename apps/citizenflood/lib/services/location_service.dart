import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';

/// Thrown when we cannot obtain a location (permission denied or GPS off).
class LocationUnavailable implements Exception {
  final String message;
  LocationUnavailable(this.message);
  @override
  String toString() => message;
}

class CapturedLocation {
  const CapturedLocation({required this.coordinates, required this.accuracyM});

  final LatLng coordinates;
  final double accuracyM;
}

class LocationService {
  /// Returns the device's current position, requesting permission if needed.
  Future<CapturedLocation> current() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw LocationUnavailable('Location services are turned off.');
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw LocationUnavailable('Location permission was denied.');
    }

    final pos = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );
    return CapturedLocation(
      coordinates: LatLng(pos.latitude, pos.longitude),
      accuracyM: pos.accuracy,
    );
  }
}
