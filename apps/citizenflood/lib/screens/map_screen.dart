import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../maps/citizen_map.dart';
import '../services/station_repository.dart';
import '../widgets/station_detail_sheet.dart';
import '../maps/map_selection.dart';
import '../models/report.dart';
import '../services/report_repository.dart';
import '../services/account_session.dart';
import '../services/location_service.dart';
import '../widgets/report_detail_sheet.dart';
import 'location_picker_screen.dart';
import 'observation_form_screen.dart';
import '../widgets/report_menu.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({
    super.key,
    this.repository,
    this.stations,
    this.session,
    this.location,
    this.onShowReports,
  });
  final VoidCallback? onShowReports;
  final LocationService? location;
  final ReportRepository? repository;
  final StationRepository? stations;
  final AccountSession? session;
  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  late final _stations = widget.stations ?? StationRepository();
  late Future<List<MonitoringStation>> _stationFuture = _stations.stations();
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

  void _refresh() => setState(() {
    _future = _repo.recent();
    _stationFuture = _stations.stations();
  });

  Future<void> _showStation(MonitoringStation station) async {
    setState(
      () => _center = SelectedLocation(
        latitude: station.latitude,
        longitude: station.longitude,
        source: LocationSource.selected,
      ),
    );
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) =>
          StationDetailSheet(station: station, repository: _stations),
    );
  }

  Future<void> _listStations(List<MonitoringStation> stations) async {
    final chosen = await showModalBottomSheet<MonitoringStation>(
      context: context,
      showDragHandle: true,
      useSafeArea: true,
      builder: (c) => SafeArea(
        child: SizedBox(
          height: MediaQuery.sizeOf(c).height * .6,
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  'Plants and stations',
                  style: Theme.of(c).textTheme.titleLarge,
                ),
              ),
              Expanded(
                child: stations.isEmpty
                    ? const Center(
                        child: Text('No monitoring stations available.'),
                      )
                    : ListView(
                        children: [
                          for (final station in stations)
                            ListTile(
                              leading: const Icon(Icons.factory_outlined),
                              title: Text(station.name),
                              subtitle: Text(station.code),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => Navigator.pop(c, station),
                            ),
                        ],
                      ),
              ),
            ],
          ),
        ),
      ),
    );
    if (mounted && chosen != null) _showStation(chosen);
  }

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
    String? kind = switch (category) {
      ReportCategory.waterLevel => 'flooding',
      ReportCategory.rainfall => 'rain_occurrence',
      ReportCategory.wastewater => 'water_appearance',
      _ => null,
    };
    if (kind == null) {
      kind = await showModalBottomSheet<String>(
        context: context,
        showDragHandle: true,
        builder: (c) => SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (final option in const [
                ('rainfall_accumulation', 'Gauge rainfall'),
                ('water_reading', 'Water reading'),
                ('temperature', 'Temperature'),
              ])
                ListTile(
                  title: Text(option.$2),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.pop(c, option.$1),
                ),
            ],
          ),
        ),
      );
      if (!mounted || kind == null) return;
    }
    final selectedKind = kind;

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
        builder: (_) => ObservationFormScreen(
          kind: selectedKind,
          location: selected,
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
                    leading: Icon(r.icon),
                    title: Text(r.label),
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
    final update = await showModalBottomSheet<bool>(
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
                onUpdate: () => Navigator.pop(c, true),
              )
            : const SizedBox.shrink();
      },
    );
    _detailRoute = null;
    if (mounted) setState(() => _selectedId = null);
    if (mounted &&
        generation == _session.generation &&
        update == true &&
        report.isOwner) {
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ObservationFormScreen(
            kind: 'flooding',
            previous: report,
            location: SelectedLocation(
              latitude: report.latitude,
              longitude: report.longitude,
              source: LocationSource.selected,
            ),
            reports: _repo,
            session: _session,
            onShowReports: widget.onShowReports,
          ),
        ),
      );
      _refresh();
    }
  }

  Future<void> _showObservations(List<Report> reports) async {
    final generation = _generation;
    final chosen = await showModalBottomSheet<Report>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (c) {
        _detailRoute = ModalRoute.of(c);
        return SafeArea(
          child: SizedBox(
            height: MediaQuery.sizeOf(c).height * .65,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    'Observations',
                    style: Theme.of(c).textTheme.titleLarge,
                  ),
                ),
                Expanded(
                  child: reports.isEmpty
                      ? const Center(child: Text('No observations yet.'))
                      : ListView.builder(
                          itemCount: reports.length,
                          itemBuilder: (_, i) {
                            final report = reports[i];
                            final observed =
                                report.observedAt ?? report.createdAt;
                            final time = observed == null
                                ? ''
                                : '\n${DateFormat('d MMM · HH:mm').format(observed.toLocal())}';
                            return ListTile(
                              leading: Icon(report.icon),
                              title: Text(report.label),
                              subtitle: Text(
                                '${report.readingLabel} · ${report.isOwner ? 'Your observation' : 'Community · approximate location'}$time',
                              ),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => Navigator.pop(c, report),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
        );
      },
    );
    _detailRoute = null;
    if (!mounted || generation != _generation || chosen == null) return;
    _showDetail(chosen, [chosen]);
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<List<Report>>(
    key: ValueKey(_generation),
    future: _future,
    builder: (context, snapshot) {
      final reports = snapshot.data ?? <Report>[];
      return FutureBuilder<List<MonitoringStation>>(
        future: _stationFuture,
        builder: (context, stationSnapshot) {
          final stations = stationSnapshot.data ?? <MonitoringStation>[];
          return Stack(
            children: [
              Positioned.fill(
                child: CitizenMap(
                  key: ValueKey(_generation),
                  resetKey: _generation,
                  center: _center,
                  deviceLocation: _device,
                  reports: reports,
                  stations: stations,
                  onStation: _showStation,
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
                child: Material(
                  elevation: 1,
                  borderRadius: BorderRadius.circular(16),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      TextButton.icon(
                        onPressed: stationSnapshot.hasError
                            ? _refresh
                            : () => _listStations(stations),
                        icon: Icon(
                          stationSnapshot.hasError
                              ? Icons.sync_problem
                              : Icons.factory_outlined,
                        ),
                        label: Text(
                          stationSnapshot.hasError
                              ? 'Retry plants'
                              : stationSnapshot.connectionState ==
                                    ConnectionState.waiting
                              ? 'Plants …'
                              : 'Plants ${stations.length}',
                        ),
                      ),
                      Tooltip(
                        message: 'List observations',
                        child: TextButton.icon(
                          onPressed: () => _showObservations(reports),
                          icon: const Icon(Icons.list_alt),
                          label: Text(
                            snapshot.connectionState == ConnectionState.waiting
                                ? '…'
                                : '${reports.length}',
                          ),
                        ),
                      ),
                      IconButton(
                        tooltip: snapshot.hasError
                            ? 'Observations unavailable. Retry'
                            : 'Refresh observations',
                        onPressed: _refresh,
                        icon: Icon(
                          snapshot.hasError
                              ? Icons.sync_problem
                              : Icons.refresh,
                        ),
                      ),
                    ],
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
    },
  );
}
