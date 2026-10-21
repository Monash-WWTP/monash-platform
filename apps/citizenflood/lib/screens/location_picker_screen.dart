import 'package:flutter/material.dart';
import '../maps/citizen_map.dart';
import '../maps/map_selection.dart';
import '../services/location_service.dart';

class LocationPickerScreen extends StatefulWidget {
  const LocationPickerScreen({super.key, this.initialLocation});
  final SelectedLocation? initialLocation;
  @override
  State<LocationPickerScreen> createState() => _LocationPickerScreenState();
}

class _LocationPickerScreenState extends State<LocationPickerScreen> {
  late SelectedLocation _center =
      widget.initialLocation ??
      const SelectedLocation(
        latitude: 3.1390,
        longitude: 101.6869,
        source: LocationSource.selected,
      );
  late SelectedLocation _selected = _center;
  SelectedLocation? _device;
  bool _locating = false;
  String? _error;
  Future<void> _locate() async {
    setState(() {
      _locating = true;
      _error = null;
    });
    try {
      final p = await LocationService().current().timeout(
        const Duration(seconds: 20),
      );
      if (!mounted) return;
      setState(() {
        _device = SelectedLocation(
          latitude: p.coordinates.latitude,
          longitude: p.coordinates.longitude,
          accuracyM: p.accuracyM,
          source: LocationSource.current,
        );
        _center = _device!;
        _selected = _device!;
      });
    } catch (_) {
      if (mounted) {
        setState(
          () => _error =
              'Could not get your location. Choose a point on the map or enable location access.',
        );
      }
    } finally {
      if (mounted) setState(() => _locating = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Choose location')),
    body: Column(
      children: [
        Expanded(
          child: Stack(
            alignment: Alignment.center,
            children: [
              CitizenMap(
                center: _center,
                deviceLocation: _device,
                onCenterChanged: (point) {
                  if ((_selected.latitude - point.latitude).abs() > 0.00001 ||
                      (_selected.longitude - point.longitude).abs() > 0.00001) {
                    setState(() => _selected = point);
                  }
                },
              ),
              const IgnorePointer(
                child: Padding(
                  padding: EdgeInsets.only(bottom: 38),
                  child: Icon(
                    Icons.location_pin,
                    size: 48,
                    color: Color(0xFF146346),
                  ),
                ),
              ),
            ],
          ),
        ),
        SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _selected.source == LocationSource.current
                                ? 'Current location'
                                : 'Selected point',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          Text(
                            '${_selected.label}${_selected.accuracyM == null ? '' : ' · ±${_selected.accuracyM!.round()} m'}',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      tooltip: _locating
                          ? 'Finding location…'
                          : 'Use current location',
                      onPressed: _locating ? null : _locate,
                      icon: _locating
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.my_location),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      _error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                FilledButton(
                  onPressed: _locating
                      ? null
                      : () => Navigator.pop(context, _selected),
                  child: const Text('Confirm location'),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
  );
}
