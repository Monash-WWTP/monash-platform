import 'dart:io';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/report_draft.dart';
import '../models/report.dart';
import '../maps/map_selection.dart';
import 'my_reports_screen.dart';

class ReportReviewScreen extends StatefulWidget {
  const ReportReviewScreen({
    super.key,
    required this.draft,
    required this.submit,
    this.onShowReports,
  });
  final VoidCallback? onShowReports;
  final ReportDraft draft;
  final Future<bool> Function() submit;
  @override
  State<ReportReviewScreen> createState() => _ReportReviewScreenState();
}

class _ReportReviewScreenState extends State<ReportReviewScreen> {
  bool _busy = false, _sent = false;
  String? _error;
  @override
  Widget build(BuildContext context) {
    final draft = widget.draft;
    return PopScope(
      canPop: !_busy && !_sent,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop && _sent) Navigator.of(context).popUntil((r) => r.isFirst);
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text(_sent ? 'Report received' : 'Review report'),
          automaticallyImplyLeading: !_busy && !_sent,
        ),
        body: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            if (_sent) ...[
              Icon(
                Icons.check_circle_outline,
                size: 56,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 20),
              Text(
                'Pending review',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              const Text(
                'Your observation has been saved. It will appear publicly only after approval.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 28),
              FilledButton(
                onPressed: () {
                  if (widget.onShowReports != null) {
                    Navigator.of(context).popUntil((r) => r.isFirst);
                    widget.onShowReports!();
                    return;
                  }
                  Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(
                      builder: (_) => Scaffold(
                        appBar: AppBar(title: const Text('My reports')),
                        body: const MyReportsScreen(),
                      ),
                    ),
                    (r) => r.isFirst,
                  );
                },
                child: const Text('View my reports'),
              ),
              TextButton(
                onPressed: () =>
                    Navigator.of(context).popUntil((r) => r.isFirst),
                child: const Text('Back to map'),
              ),
            ] else ...[
              Text(
                draft.category.label,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 12),
              Text(
                draft.reading,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 24),
              const Divider(),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.place_outlined),
                title: const Text('Location'),
                subtitle: Text(
                  '${draft.location.label}\n${draft.location.source == LocationSource.current ? 'Current location' : 'Selected point'}${draft.location.accuracyM != null ? ' · ±${draft.location.accuracyM!.round()} m' : ''}',
                ),
              ),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.schedule),
                title: const Text('Observed'),
                subtitle: Text(
                  DateFormat(
                    'd MMM yyyy · h:mm a',
                  ).format(draft.observedAt.toLocal()),
                ),
              ),
              if (draft.note?.isNotEmpty ?? false)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.notes),
                  title: const Text('Note'),
                  subtitle: Text(draft.note!),
                ),
              if (draft.photoPath != null) ...[
                const SizedBox(height: 16),
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.file(
                    File(draft.photoPath!),
                    height: 180,
                    fit: BoxFit.cover,
                    errorBuilder: (_, _, _) => const Text('Photo attached'),
                  ),
                ),
              ],
              const SizedBox(height: 24),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ),
              FilledButton(
                onPressed: _busy
                    ? null
                    : () async {
                        setState(() {
                          _busy = true;
                          _error = null;
                        });
                        final sent = await widget.submit();
                        if (mounted) {
                          setState(() {
                            _busy = false;
                            _sent = sent;
                            if (!sent) {
                              _error =
                                  'Report not confirmed. Retry with the same details, or go back to edit.';
                            }
                          });
                        }
                      },
                child: _busy
                    ? const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          SizedBox(width: 12),
                          Text('Submitting…'),
                        ],
                      )
                    : const Text('Submit report'),
              ),
              TextButton(
                onPressed: _busy ? null : () => Navigator.pop(context),
                child: const Text('Edit report'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
