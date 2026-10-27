import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/report.dart';
import '../services/depth_preview.dart';
import '../screens/depth_preview_screen.dart';
import '../services/report_repository.dart';

class ReportDetailSheet extends StatelessWidget {
  const ReportDetailSheet({
    super.key,
    required this.report,
    required this.ownerView,
    this.repository,
    this.onUpdate,
  });
  final VoidCallback? onUpdate;
  final Report report;
  final bool ownerView;
  final ReportRepository? repository;
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final depthPreview = ownerView && report.isOwner
        ? DepthPreview.fromObservation(report.observation?.data)
        : null;
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(24, 0, 24, 28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(report.icon, color: theme.colorScheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(report.label, style: theme.textTheme.titleLarge),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(report.readingLabel, style: theme.textTheme.headlineMedium),
            if (report.observation != null)
              for (final line in report.observationContext)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(line),
                ),
            if (report.observation == null)
              const Padding(
                padding: EdgeInsets.only(top: 8),
                child: Text('Legacy report · measurement context unspecified'),
              ),
            const SizedBox(height: 8),
            Text(
              DateFormat('d MMM yyyy · h:mm a').format(
                (report.observedAt ?? report.createdAt ?? DateTime.now())
                    .toLocal(),
              ),
            ),
            const SizedBox(height: 12),
            Text(
              ownerView
                  ? '${report.moderationStatus.name[0].toUpperCase()}${report.moderationStatus.name.substring(1)} · Your report'
                  : 'Community observation · Approximate location',
            ),
            const SizedBox(height: 12),
            Text(
              '${report.latitude.toStringAsFixed(ownerView ? 5 : 2)}, ${report.longitude.toStringAsFixed(ownerView ? 5 : 2)}',
            ),
            if (ownerView &&
                report.isOwner &&
                report.id != null &&
                report.observation?.kind == 'flooding' &&
                onUpdate != null)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: OutlinedButton.icon(
                  onPressed: onUpdate,
                  icon: const Icon(Icons.update),
                  label: const Text('Report an update'),
                ),
              ),
            if (depthPreview != null)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: OutlinedButton.icon(
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute<void>(
                      builder: (_) => DepthPreviewScreen(
                        preview: depthPreview,
                        contextLabel: report.observedAt == null
                            ? 'Reported depth · observation time unavailable'
                            : 'Reported depth · ${DateFormat('d MMM y · HH:mm').format(report.observedAt!.toLocal())}',
                      ),
                    ),
                  ),
                  icon: const Icon(Icons.view_in_ar),
                  label: const Text('Visualise reported depth'),
                ),
              ),
            if (ownerView && report.reviewReason != null) ...[
              const SizedBox(height: 16),
              Text('Review reason', style: theme.textTheme.titleSmall),
              const SizedBox(height: 4),
              Text(report.reviewReason!),
            ],
            if (report.note?.isNotEmpty ?? false) ...[
              const SizedBox(height: 16),
              Text(report.note!),
            ],
            if (ownerView && report.photoPath != null) ...[
              const SizedBox(height: 16),
              FutureBuilder<Uint8List>(
                future: (repository ?? ReportRepository()).photoBytes(
                  report.photoPath!,
                ),
                builder: (context, snapshot) {
                  if (snapshot.hasError) {
                    return const Text(
                      'Photo unavailable. Reopen this report to retry.',
                    );
                  }
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
                      errorBuilder: (_, _, _) =>
                          const Text('Photo unavailable'),
                    ),
                  );
                },
              ),
            ],
          ],
        ),
      ),
    );
  }
}
