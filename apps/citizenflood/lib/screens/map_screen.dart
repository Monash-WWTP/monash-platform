import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:intl/intl.dart';

import '../models/report.dart';
import '../services/report_repository.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});
  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final _repo = ReportRepository();
  late Future<List<Report>> _future = _repo.recent();
  final _mapController = MapController();

  Color _pinColor(ReportCategory c) => switch (c) {
    ReportCategory.rainfall => const Color(0xFF3399FF),
    ReportCategory.waterLevel => const Color(0xFF00AACC),
    ReportCategory.temperature => const Color(0xFFFF6633),
    ReportCategory.wastewater => const Color(0xFF8855CC),
  };

  void _refresh() => setState(() => _future = _repo.recent());

  String _time(Report r) => r.createdAt == null
      ? ''
      : DateFormat('d MMM, h:mm a').format(r.createdAt!.toLocal());

  void _showDetail(Report r) {
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (_) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(r.category.emoji, style: const TextStyle(fontSize: 28)),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    r.category.label,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              r.readingLabel,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: _pinColor(r.category),
              ),
            ),
            const SizedBox(height: 4),
            Text(_time(r), style: Theme.of(context).textTheme.bodySmall),
            if (r.note != null && r.note!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(r.note!, style: Theme.of(context).textTheme.bodyMedium),
            ],
            if (r.photoPath != null) ...[
              const SizedBox(height: 16),
              FutureBuilder<Uint8List>(
                future: _repo.photoBytes(r.photoPath!),
                builder: (_, snapshot) {
                  if (snapshot.hasError) return const Text('Photo unavailable');
                  if (!snapshot.hasData) {
                    return const SizedBox(
                      height: 80,
                      child: Center(child: CircularProgressIndicator()),
                    );
                  }
                  return ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.memory(
                      snapshot.data!,
                      height: 220,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      errorBuilder: (_, _, _) => const SizedBox(
                        height: 60,
                        child: Center(child: Text('Photo unavailable')),
                      ),
                    ),
                  );
                },
              ),
            ],
            if (r.moderationStatus == ModerationStatus.pending) ...[
              const SizedBox(height: 12),
              const Chip(
                avatar: Icon(Icons.schedule, size: 16),
                label: Text('Pending review'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: FloatingActionButton.small(
        onPressed: _refresh,
        tooltip: 'Refresh',
        child: const Icon(Icons.refresh),
      ),
      body: FutureBuilder<List<Report>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Could not load readings.'),
                  TextButton(onPressed: _refresh, child: const Text('Retry')),
                ],
              ),
            );
          }
          final reports = snap.data ?? [];
          final center = reports.isNotEmpty
              ? LatLng(reports.first.latitude, reports.first.longitude)
              : const LatLng(3.1390, 101.6869); // Kuala Lumpur fallback

          return Column(
            children: [
              Expanded(
                child: FlutterMap(
                  mapController: _mapController,
                  options: MapOptions(initialCenter: center, initialZoom: 12),
                  children: [
                    TileLayer(
                      urlTemplate:
                          'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      userAgentPackageName: 'au.edu.monash.citizenflood',
                    ),
                    RichAttributionWidget(
                      attributions: [
                        TextSourceAttribution('© OpenStreetMap contributors'),
                      ],
                    ),
                    MarkerLayer(
                      markers: [
                        for (final r in reports)
                          Marker(
                            point: LatLng(r.latitude, r.longitude),
                            width: 40,
                            height: 40,
                            child: GestureDetector(
                              onTap: () => _showDetail(r),
                              child: Icon(
                                Icons.location_on,
                                color: _pinColor(r.category),
                                size: 40,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              SizedBox(
                height: 170,
                child: reports.isEmpty
                    ? const Center(
                        child: Text('No readings yet — be the first!'),
                      )
                    : ListView(
                        children: [
                          for (final r in reports.take(20))
                            ListTile(
                              dense: true,
                              onTap: () {
                                _mapController.move(
                                  LatLng(r.latitude, r.longitude),
                                  15,
                                );
                                _showDetail(r);
                              },
                              leading: Text(
                                r.category.emoji,
                                style: const TextStyle(fontSize: 22),
                              ),
                              title: Text(
                                '${r.category.label} · ${r.readingLabel}',
                              ),
                              subtitle: Text(_time(r)),
                              trailing: r.photoPath != null
                                  ? const Icon(Icons.photo_outlined, size: 18)
                                  : null,
                            ),
                        ],
                      ),
              ),
            ],
          );
        },
      ),
    );
  }
}
