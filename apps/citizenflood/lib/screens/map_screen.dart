import 'package:flutter/material.dart';
import '../maps/citizen_map.dart';
import '../maps/map_selection.dart';
import '../models/report.dart';
import '../services/report_repository.dart';
import '../services/account_session.dart';
import '../services/location_service.dart';
import '../widgets/report_detail_sheet.dart';
import 'location_picker_screen.dart';
import 'report_form_screen.dart';
import '../widgets/report_menu.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({
    super.key,
    this.repository,
    this.session,
    this.location,
    this.onShowReports,
  });
  final VoidCallback? onShowReports;
  final LocationService? location;
  final ReportRepository? repository;
  final AccountSession? session;
  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  late final _repo = widget.repository ?? ReportRepository();
  late final _session = widget.session ?? AccountSession.instance;
  late Future<List<Report>> _future = _repo.recent();
  late int _generation = _session.generation;
  ModalRoute<dynamic>? _detailRoute;
  String? _selectedId;
  SelectedLocation _center = const SelectedLocation(
    latitude: 3.1390,
    longitude: 101.6869,
    source: LocationSource.selected,
  );
  SelectedLocation? _device;
  SelectedLocation? _viewportCenter;
  bool _locating = false;
  @override
  void initState() {
    super.initState();
    _session.addListener(_changed);
  }

  void _changed() {
    if (_generation == _session.generation) return;
    _generation = _session.generation;
    final route = _detailRoute;
    _detailRoute = null;
    if (route?.isActive ?? false) route!.navigator?.removeRoute(route);
    setState(() {
      _locating = false;
      _selectedId = null;
      _device = null;
      _viewportCenter = null;
      _center = const SelectedLocation(
        latitude: 3.1390,
        longitude: 101.6869,
        source: LocationSource.selected,
      );
      _future = _repo.recent();
    });
  }

  @override
  void dispose() {
    _session.removeListener(_changed);
    super.dispose();
  }

  void _refresh() => setState(() => _future = _repo.recent());
  Future<void> _locate() async {
    final generation = _generation;
    setState(() => _locating = true);
    try {
      final p = await (widget.location ?? LocationService()).current().timeout(
        const Duration(seconds: 20),
      );
      if (!mounted || generation != _generation) return;
      setState(() {
        _device = SelectedLocation(
          latitude: p.coordinates.latitude,
          longitude: p.coordinates.longitude,
          accuracyM: p.accuracyM,
          source: LocationSource.current,
        );
        _center = _device!;
      });
    } catch (_) {
      if (mounted && generation == _generation) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Location unavailable. You can still choose a point on the map.',
            ),
          ),
        );
      }
    } finally {
      if (mounted && generation == _generation) {
        setState(() => _locating = false);
      }
    }
  }

  Future<void> _report(ReportCategory category) async {
    final selected = await Navigator.push<SelectedLocation>(
      context,
      MaterialPageRoute(
        builder: (_) => LocationPickerScreen(
          initialLocation: _viewportCenter ?? _device ?? _center,
        ),
      ),
    );
    if (!mounted || selected == null) return;
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ReportFormScreen(
          category: category,
          selectedLocation: selected,
          onShowReports: widget.onShowReports,
        ),
      ),
    );
    _refresh();
  }

  void _showDetail(Report report, List<Report> reports) async {
    final generation = _generation;
    final nearby = reports
        .where(
          (r) =>
              (r.latitude - report.latitude).abs() < 0.00015 &&
              (r.longitude - report.longitude).abs() < 0.00015,
        )
        .toList();
    if (nearby.length > 1) {
      final chosen = await showModalBottomSheet<Report>(
        context: context,
        showDragHandle: true,
        builder: (c) {
          _detailRoute = ModalRoute.of(c);
          return SafeArea(
            child: ListView(
              shrinkWrap: true,
              children: [
                const ListTile(title: Text('Observations at this location')),
                for (final r in nearby)
                  ListTile(
                    leading: Icon(r.category.icon),
                    title: Text(r.category.label),
                    subtitle: Text(r.readingLabel),
                    onTap: () => Navigator.pop(c, r),
                  ),
              ],
            ),
          );
        },
      );
      _detailRoute = null;
      if (!mounted || generation != _generation || chosen == null) return;
      report = chosen;
    }
    setState(() {
      _selectedId = report.id;
      _center = SelectedLocation(
        latitude: report.latitude,
        longitude: report.longitude,
        source: LocationSource.selected,
      );
    });
    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (c) {
        _detailRoute = ModalRoute.of(c);
        return generation == _session.generation
            ? ReportDetailSheet(
                report: report,
                ownerView: report.isOwner,
                repository: _repo,
              )
            : const SizedBox.shrink();
      },
    );
    _detailRoute = null;
    if (mounted) setState(() => _selectedId = null);
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<List<Report>>(
    key: ValueKey(_generation),
    future: _future,
    builder: (context, snapshot) {
      final reports = snapshot.data ?? <Report>[];
      return Stack(
        children: [
          Positioned.fill(
            child: CitizenMap(
              key: ValueKey(_generation),
              resetKey: _generation,
              center: _center,
              deviceLocation: _device,
              reports: reports,
              selectedId: _selectedId,
              onObservation: (r) => _showDetail(r, reports),
              onCenterChanged: (p) {
                _viewportCenter = p;
              },
            ),
          ),
          Positioned(
            top: 12,
            left: 16,
            right: 76,
            child: Material(
              elevation: 1,
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 10,
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.circle,
                      size: 10,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        snapshot.hasError
                            ? 'Observations unavailable'
                            : snapshot.connectionState ==
                                  ConnectionState.waiting
                            ? 'Loading observations…'
                            : '${reports.length} ${reports.length == 1 ? 'observation' : 'observations'}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                    IconButton(
                      tooltip: 'Refresh observations',
                      onPressed: _refresh,
                      icon: const Icon(Icons.refresh),
                      visualDensity: VisualDensity.compact,
                    ),
                  ],
                ),
              ),
            ),
          ),
          Positioned(
            top: 12,
            right: 16,
            child: FloatingActionButton.small(
              heroTag: 'locate',
              tooltip: 'Use current location',
              onPressed: _locating ? null : _locate,
              child: _locating
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.my_location),
            ),
          ),
          Positioned(
            bottom: 20,
            right: 20,
            child: ReportMenu(onSelected: _report),
          ),
        ],
      );
    },
  );
}
