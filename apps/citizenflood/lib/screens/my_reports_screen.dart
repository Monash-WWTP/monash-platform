import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/account_session.dart';
import '../models/report.dart';
import '../services/report_repository.dart';
import '../widgets/report_detail_sheet.dart';

class MyReportsScreen extends StatefulWidget {
  const MyReportsScreen({
    super.key,
    this.repository,
    this.session,
    this.active = true,
  });
  final bool active;
  final ReportRepository? repository;
  final AccountSession? session;
  @override
  State<MyReportsScreen> createState() => _MyReportsScreenState();
}

class _MyReportsScreenState extends State<MyReportsScreen> {
  late final _session = widget.session ?? AccountSession.instance;
  late final _repo = widget.repository ?? ReportRepository();
  Future<ReportPage>? _future;
  int _offset = 0, _generation = 0;
  ModalRoute<dynamic>? _detail;
  @override
  void initState() {
    super.initState();
    _generation = _session.generation;
    _session.addListener(_changed);
    _load();
  }

  void _load() {
    _future = widget.active && _session.signedIn
        ? _repo.own(offset: _offset)
        : null;
  }

  @override
  void didUpdateWidget(covariant MyReportsScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active && !oldWidget.active) {
      _offset = 0;
      _load();
    }
  }

  void _changed() {
    if (_generation == _session.generation) return;
    _generation = _session.generation;
    final detail = _detail;
    _detail = null;
    if (detail?.isActive ?? false) detail!.navigator?.removeRoute(detail);
    setState(() {
      _offset = 0;
      _load();
    });
  }

  @override
  void dispose() {
    _session.removeListener(_changed);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.active) return const SizedBox.shrink();
    if (!_session.signedIn) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.receipt_long_outlined, size: 40),
              const SizedBox(height: 16),
              Text(
                'Your observations, in one place',
                style: Theme.of(context).textTheme.titleLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              const Text(
                'Sign in to see your submitted reports and their review status.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: () async {
                  try {
                    await _session.signIn();
                  } catch (_) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text(
                            'Sign-in did not finish. Please try again.',
                          ),
                        ),
                      );
                    }
                  }
                },
                child: const Text('Sign in'),
              ),
            ],
          ),
        ),
      );
    }
    final generation = _generation;
    return FutureBuilder<ReportPage>(
      key: ValueKey(generation),
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Could not load your reports.'),
                TextButton(
                  onPressed: () => setState(_load),
                  child: const Text('Retry'),
                ),
              ],
            ),
          );
        }
        if (!snapshot.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        final page = snapshot.data!;
        return RefreshIndicator(
          onRefresh: () async {
            setState(_load);
            await _future;
          },
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            children: [
              if (page.items.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 64, horizontal: 16),
                  child: Text(
                    'No reports yet. Choose a location on the map to record your first observation.',
                    textAlign: TextAlign.center,
                  ),
                ),
              for (final report in page.items) ...[
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                    vertical: 8,
                    horizontal: 8,
                  ),
                  leading: Icon(
                    report.category.icon,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  title: Text(report.category.label),
                  subtitle: Text(
                    '${report.readingLabel}\n${DateFormat('d MMM · h:mm a').format((report.observedAt ?? report.createdAt ?? DateTime.now()).toLocal())}',
                  ),
                  isThreeLine: true,
                  trailing: Chip(
                    label: Text(
                      report.moderationStatus.name[0].toUpperCase() +
                          report.moderationStatus.name.substring(1),
                    ),
                  ),
                  onTap: () => showModalBottomSheet(
                    context: context,
                    showDragHandle: true,
                    isScrollControlled: true,
                    useSafeArea: true,
                    builder: (c) {
                      _detail = ModalRoute.of(c);
                      return generation == _session.generation
                          ? ReportDetailSheet(
                              report: report,
                              ownerView: true,
                              repository: _repo,
                            )
                          : const SizedBox.shrink();
                    },
                  ),
                ),
                const Divider(height: 1),
              ],
              if (page.total > 25)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    TextButton(
                      onPressed: _offset == 0
                          ? null
                          : () => setState(() {
                              _offset -= 25;
                              _load();
                            }),
                      child: const Text('Previous'),
                    ),
                    Text(
                      '${_offset + 1}–${_offset + page.items.length} of ${page.total}',
                    ),
                    TextButton(
                      onPressed: _offset + page.items.length >= page.total
                          ? null
                          : () => setState(() {
                              _offset += 25;
                              _load();
                            }),
                      child: const Text('Next'),
                    ),
                  ],
                ),
            ],
          ),
        );
      },
    );
  }
}
