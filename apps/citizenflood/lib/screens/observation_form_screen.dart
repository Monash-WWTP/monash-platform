import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:uuid/uuid.dart';
import '../maps/map_selection.dart';
import '../models/observation.dart';
import '../services/account_session.dart';
import '../services/observation_repository.dart';
import '../services/report_repository.dart';
import '../widgets/measurement_fields.dart';
import 'location_picker_screen.dart';
import 'report_review_screen.dart';

class ObservationFormScreen extends StatefulWidget {
  const ObservationFormScreen({
    super.key,
    required this.kind,
    required this.location,
    this.repository,
    this.reports,
    this.session,
    this.onShowReports,
  });
  final String kind;
  final SelectedLocation location;
  final ObservationRepository? repository;
  final ReportRepository? reports;
  final AccountSession? session;
  final VoidCallback? onShowReports;
  @override
  State<ObservationFormScreen> createState() => _ObservationFormScreenState();
}

class _ObservationFormScreenState extends State<ObservationFormScreen> {
  late final _repo = widget.repository ?? ObservationRepository();
  late final _reports = widget.reports ?? ReportRepository();
  late final _session = widget.session ?? AccountSession.instance;
  final _form = GlobalKey<FormState>();
  final _measurement = GlobalKey<MeasurementFieldsState>();
  final _note = TextEditingController();
  late SelectedLocation _location = widget.location;
  Future<bool>? _capability;
  List<Map<String, dynamic>> _references = [];
  String? _response, _photo, _media, _mediaPhoto, _error;
  final _features = <String>{};
  DateTime? _observed;
  String? _key;
  bool _reviewing = false, _authenticating = false, _invalidated = false;
  bool _referencesLoading = false;
  late int _draftGeneration;
  int? _boundGeneration;
  ObservationDraft? _pendingDraft;
  bool get _quantitative => ![
    'flooding',
    'rain_occurrence',
    'water_appearance',
  ].contains(widget.kind);
  @override
  void initState() {
    super.initState();
    _draftGeneration = _session.generation;
    _session.addListener(_accountChanged);
    _capability = _load();
  }

  void _accountChanged() {
    if (_authenticating ||
        _session.generation == _draftGeneration ||
        _invalidated) {
      return;
    }
    _invalidated = true;
    _media = null;
    _mediaPhoto = null;
    _photo = null;
    _key = null;
    _pendingDraft = null;
    _note.clear();
    if (mounted) {
      setState(() {});
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) Navigator.of(context).popUntil((r) => r.isFirst);
      });
    }
  }

  Future<bool> _load() async {
    final supported = await _repo.supported();
    if (supported && widget.kind == 'water_reading' && _session.signedIn) {
      _references = await _repo.references();
    }
    return supported;
  }

  Future<void> _loadReferences() async {
    if (_referencesLoading) return;
    setState(() => _referencesLoading = true);
    try {
      if (!_session.signedIn) {
        _authenticating = true;
        try {
          await _session.signIn();
        } finally {
          _authenticating = false;
        }
        _draftGeneration = _session.generation;
      }
      if (!_session.signedIn || _invalidated) return;
      final generation = _session.generation;
      final refs = await _repo.references();
      if (mounted && !_invalidated && generation == _session.generation) {
        setState(() => _references = refs);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not load gauge references. Try again.');
      }
    } finally {
      if (mounted) setState(() => _referencesLoading = false);
    }
  }

  @override
  void dispose() {
    _session.removeListener(_accountChanged);
    _note.dispose();
    super.dispose();
  }

  void _changed() {
    _pendingDraft = null;
    _key = null;
  }

  Future<void> _choosePhoto(ImageSource source) async {
    try {
      final photo = await ImagePicker().pickImage(
        source: source,
        maxWidth: 1920,
        imageQuality: 85,
      );
      if (photo != null && mounted) {
        setState(() {
          _photo = photo.path;
          _media = null;
          _changed();
        });
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Photo unavailable. You can report without it.'),
          ),
        );
      }
    }
  }

  Future<void> _time() async {
    final now = DateTime.now();
    final initial = _observed ?? now;
    final date = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2000),
      lastDate: now,
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(initial),
    );
    if (time != null && mounted) {
      setState(() {
        _observed = DateTime(
          date.year,
          date.month,
          date.day,
          time.hour,
          time.minute,
        );
        _changed();
      });
    }
  }

  Future<void> _review() async {
    if (_invalidated || _reviewing || !_form.currentState!.validate()) return;
    Map<String, dynamic>? observation;
    if (_quantitative) {
      observation = _measurement.currentState!.observation();
    } else {
      if (_response == null) {
        setState(() => _error = 'Choose what you observed, or Unsure.');
        return;
      }
      final field = widget.kind == 'water_appearance' ? 'features' : 'surfaces';
      if ((widget.kind == 'flooding' && _response == 'present' ||
              _response == 'features_observed') &&
          _features.isEmpty) {
        setState(() => _error = 'Choose the observed feature.');
        return;
      }
      observation = {
        'kind': widget.kind,
        'method': 'visual',
        'response': _response,
        if (widget.kind != 'rain_occurrence') field: _features.toList(),
      };
    }
    if (observation == null) return;
    final observed = _pendingDraft?.observedAt ?? _observed ?? DateTime.now();
    if (observed.isAfter(DateTime.now().add(const Duration(minutes: 5)))) {
      setState(() => _error = 'Observation time cannot be in the future.');
      return;
    }
    if (widget.kind == 'rainfall_accumulation' &&
        DateTime.parse(observation['interval_end']).isAfter(observed)) {
      setState(
        () => _error = 'Collection must end before the observation time.',
      );
      return;
    }
    final draft = _pendingDraft ??= ObservationDraft({
      'protocol_id': 'citizen-observation',
      'protocol_revision': 1,
      'observation': observation,
      'latitude': _location.latitude,
      'longitude': _location.longitude,
      'location_source': _location.source.name,
      'location_accuracy_m': _location.accuracyM,
      'observed_at': observed.toUtc().toIso8601String(),
      'note': _note.text.trim().isEmpty ? null : _note.text.trim(),
    }, photoPath: _photo);
    final key = _key ??= const Uuid().v4();
    setState(() {
      _reviewing = true;
      _error = null;
    });
    String? submissionError;
    Future<bool> submit() async {
      try {
        if (_invalidated) {
          throw StateError('Account changed. Start a new report.');
        }
        if (!_session.signedIn) {
          _authenticating = true;
          try {
            await _session.signIn();
          } finally {
            _authenticating = false;
          }
          _draftGeneration = _session.generation;
        }
        if (!_session.signedIn) throw StateError('Sign in before submitting.');
        _boundGeneration ??= _session.generation;
        final generation = _boundGeneration!;
        if (_invalidated || generation != _session.generation) {
          throw StateError('Account changed. Start a new report.');
        }
        if (draft.photoPath != null) {
          if (_mediaPhoto != draft.photoPath) {
            _media = null;
          }
          if (_media == null) {
            final bytes = await File(draft.photoPath!).readAsBytes();
            if (generation != _session.generation) {
              throw StateError('Account changed. Reopen your report.');
            }
            final uploaded = await _reports.uploadPhoto(
              bytes,
              draft.photoPath!.split('.').last,
            );
            if (_invalidated || generation != _session.generation) {
              throw StateError('Account changed. Start a new report.');
            }
            _media = uploaded;
            _mediaPhoto = draft.photoPath;
          }
        }
        if (generation != _session.generation) {
          throw StateError('Account changed. Reopen your report.');
        }
        await _repo.submit(
          ObservationDraft({...draft.payload, 'media_id': _media}),
          key,
        );
        if (generation != _session.generation) {
          throw StateError(
            'Account changed. Check My reports after signing in.',
          );
        }
        return true;
      } catch (e) {
        submissionError = e is StateError
            ? e.message.toString()
            : 'Could not confirm the report. Check your connection and retry.';
        return false;
      }
    }

    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ReportReviewScreen(
          draft: draft,
          submit: submit,
          submissionError: () => submissionError,
          onShowReports: widget.onShowReports,
        ),
      ),
    );
    if (mounted) {
      setState(() {
        _reviewing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: Text(observationLabels[widget.kind] ?? 'Observation'),
    ),
    body: _invalidated
        ? const Center(
            child: Text('Account changed. Start a new report from the map.'),
          )
        : FutureBuilder<bool>(
            future: _capability,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError || snapshot.data != true) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text(
                          'The reporting update is unavailable on this service. Your location is kept.',
                        ),
                        TextButton(
                          onPressed: () {
                            _repo.retryDiscovery();
                            setState(() => _capability = _load());
                          },
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                );
              }
              return Form(
                key: _form,
                child: ListView(
                  padding: const EdgeInsets.all(20),
                  children: [
                    if (widget.kind == 'water_reading')
                      TextButton(
                        onPressed: _referencesLoading ? null : _loadReferences,
                        child: Text(
                          _referencesLoading
                              ? 'Loading gauge references…'
                              : _session.signedIn
                              ? 'Refresh gauge references'
                              : 'Sign in for gauge references',
                        ),
                      ),
                    if (_quantitative)
                      MeasurementFields(
                        key: _measurement,
                        kind: widget.kind,
                        references: _references,
                        onChanged: _changed,
                      )
                    else ...[
                      Text(switch (widget.kind) {
                        'flooding' =>
                          'Is water covering normally dry ground here?',
                        'rain_occurrence' => 'Is it raining here now?',
                        _ => 'What can you see?',
                      }, style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 12),
                      RadioGroup<String>(
                        groupValue: _response,
                        onChanged: (v) => setState(() {
                          _response = v;
                          _features.clear();
                          _error = null;
                          _changed();
                        }),
                        child: Column(
                          children: [
                            for (final option
                                in widget.kind == 'water_appearance'
                                    ? const [
                                        (
                                          'features_observed',
                                          'Visible feature',
                                        ),
                                        ('not_observed', 'None observed here'),
                                        ('unknown', 'Unsure'),
                                      ]
                                    : const [
                                        ('present', 'Observed'),
                                        ('not_observed', 'Not observed here'),
                                        ('unknown', 'Unsure'),
                                      ])
                              RadioListTile<String>(
                                contentPadding: EdgeInsets.zero,
                                value: option.$1,
                                title: Text(option.$2),
                              ),
                          ],
                        ),
                      ),
                      if (widget.kind == 'flooding' && _response == 'present' ||
                          widget.kind == 'water_appearance' &&
                              _response == 'features_observed')
                        Wrap(
                          spacing: 8,
                          children: [
                            for (final f
                                in widget.kind == 'flooding'
                                    ? const [
                                        'road',
                                        'path',
                                        'property',
                                        'other',
                                      ]
                                    : const [
                                        'discoloration',
                                        'foam',
                                        'debris',
                                        'sheen',
                                        'overflow',
                                        'other',
                                      ])
                              FilterChip(
                                label: Text(
                                  f[0].toUpperCase() + f.substring(1),
                                ),
                                selected: _features.contains(f),
                                onSelected: (selected) => setState(() {
                                  selected
                                      ? _features.add(f)
                                      : _features.remove(f);
                                  _changed();
                                }),
                              ),
                          ],
                        ),
                    ],
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.schedule),
                      title: const Text('Observed'),
                      subtitle: Text(
                        _observed == null
                            ? 'Now'
                            : DateFormat('d MMM y · HH:mm').format(_observed!),
                      ),
                      trailing: const Icon(Icons.edit_outlined),
                      onTap: _time,
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.place_outlined),
                      title: Text(
                        _location.source == LocationSource.current
                            ? 'Current location'
                            : 'Selected point',
                      ),
                      subtitle: Text(_location.label),
                      trailing: const Icon(Icons.edit_outlined),
                      onTap: () async {
                        final p = await Navigator.push<SelectedLocation>(
                          context,
                          MaterialPageRoute(
                            builder: (_) => LocationPickerScreen(
                              initialLocation: _location,
                            ),
                          ),
                        );
                        if (p != null && mounted) {
                          setState(() {
                            _location = p;
                            _changed();
                          });
                        }
                      },
                    ),
                    ExpansionTile(
                      title: const Text('Photo and note'),
                      tilePadding: EdgeInsets.zero,
                      children: [
                        if (_photo != null)
                          Image.file(
                            File(_photo!),
                            height: 160,
                            fit: BoxFit.contain,
                          ),
                        Row(
                          children: [
                            Expanded(
                              child: TextButton.icon(
                                onPressed: () =>
                                    _choosePhoto(ImageSource.camera),
                                icon: const Icon(Icons.camera_alt_outlined),
                                label: const Text('Camera'),
                              ),
                            ),
                            Expanded(
                              child: TextButton.icon(
                                onPressed: () =>
                                    _choosePhoto(ImageSource.gallery),
                                icon: const Icon(Icons.photo_outlined),
                                label: const Text('Gallery'),
                              ),
                            ),
                          ],
                        ),
                        if (_photo != null)
                          TextButton(
                            onPressed: () => setState(() {
                              _photo = null;
                              _media = null;
                              _mediaPhoto = null;
                              _changed();
                            }),
                            child: const Text('Remove photo'),
                          ),
                        TextFormField(
                          controller: _note,
                          maxLength: 2000,
                          maxLines: 3,
                          onChanged: (_) => _changed(),
                          decoration: const InputDecoration(
                            labelText: 'Note (optional)',
                          ),
                        ),
                      ],
                    ),
                    if (_error != null)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        child: Text(
                          _error!,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.error,
                          ),
                        ),
                      ),
                    const SizedBox(height: 20),
                    FilledButton(
                      onPressed: _reviewing ? null : _review,
                      child: const Text('Review report'),
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              );
            },
          ),
  );
}
