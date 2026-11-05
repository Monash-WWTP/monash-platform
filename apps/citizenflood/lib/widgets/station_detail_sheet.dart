import 'package:flutter/material.dart';
import '../services/station_repository.dart';

class StationDetailSheet extends StatefulWidget {
  const StationDetailSheet({
    super.key,
    required this.station,
    required this.repository,
  });
  final MonitoringStation station;
  final StationRepository repository;
  @override
  State<StationDetailSheet> createState() => _StationDetailSheetState();
}

class _StationDetailSheetState extends State<StationDetailSheet> {
  late Future<Map<String, dynamic>?> _sample = widget.repository.latestSample(
    widget.station.code,
  );
  @override
  Widget build(BuildContext context) => SafeArea(
    child: SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            widget.station.name,
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          Text(
            [
              widget.station.code,
              widget.station.process,
            ].whereType<String>().where((s) => s.isNotEmpty).join(' · '),
          ),
          const SizedBox(height: 16),
          FutureBuilder<Map<String, dynamic>?>(
            future: _sample,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const LinearProgressIndicator();
              }
              if (snapshot.hasError) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Monitoring measurements unavailable.'),
                    TextButton(
                      onPressed: () => setState(
                        () => _sample = widget.repository.latestSample(
                          widget.station.code,
                        ),
                      ),
                      child: const Text('Retry'),
                    ),
                  ],
                );
              }
              final row = snapshot.data;
              if (row == null) {
                return const Text('No laboratory samples available.');
              }
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Latest laboratory sample · ${row['sample_date']}'),
                  if (row['sample_point'] != null)
                    Text('Sample point: ${row['sample_point']}'),
                  const SizedBox(height: 8),
                  for (final metric in const [
                    ('bod', 'BOD₅', 'mg/L'),
                    ('cod', 'COD', 'mg/L'),
                    ('tss', 'TSS', 'mg/L'),
                    ('nh3n', 'Ammonia-N', 'mg/L'),
                    ('no3n', 'Nitrate-N', 'mg/L'),
                    ('ph', 'pH', ''),
                    ('temperature', 'Temperature', '°C'),
                  ])
                    if (row[metric.$1] != null)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 5),
                        child: Text(
                          '${metric.$2}: ${row['${metric.$1}_bdl'] == true ? 'Below detection limit · reported ' : ''}${row[metric.$1]} ${metric.$3}',
                        ),
                      ),
                  const SizedBox(height: 12),
                  const Text(
                    'Historical laboratory measurements, not live readings or simulation results.',
                  ),
                ],
              );
            },
          ),
        ],
      ),
    ),
  );
}
