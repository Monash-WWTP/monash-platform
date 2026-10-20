import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import '../models/report.dart';
import '../theme/app_theme.dart';
import '../services/location_service.dart';
import '../services/report_repository.dart';
import '../services/account_session.dart';
import 'package:uuid/uuid.dart';

class ReportFormScreen extends StatefulWidget {
  const ReportFormScreen({
    super.key,
    required this.category,
    this.repository,
    this.location,
    this.session,
    this.imagePicker,
  });
  final ImagePicker? imagePicker;
  final ReportRepository? repository;
  final LocationService? location;
  final AccountSession? session;
  final ReportCategory category;

  @override
  State<ReportFormScreen> createState() => _ReportFormScreenState();
}

class _ReportFormScreenState extends State<ReportFormScreen> {
  late final _imagePicker = widget.imagePicker ?? ImagePicker();
  late final _location = widget.location ?? LocationService();
  late final _repo = widget.repository ?? ReportRepository();
  late final _session = widget.session ?? AccountSession.instance;
  final _noteController = TextEditingController();
  final _valueController = TextEditingController();

  Condition _condition = Condition.normal;
  XFile? _photo;
  CapturedLocation? _position;
  String? _locationError;
  bool _submitting = false;
  String? _retryKey;
  Report? _retryReport;

  bool get _isNumeric => widget.category.isNumeric;

  @override
  void initState() {
    super.initState();
    _valueController.addListener(_resetRetry);
    _noteController.addListener(_resetRetry);
    _captureLocation();
  }

  void _resetRetry() {
    if (!_submitting) {
      _retryReport = null;
      _retryKey = null;
    }
  }

  Future<void> _captureLocation() async {
    try {
      final pos = await _location.current();
      if (!mounted || _submitting) return;
      setState(() {
        _resetRetry();
        _position = pos;
        _locationError = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _locationError = e.toString());
    }
  }

  Future<void> _pickPhoto(ImageSource source) async {
    final picked = await _imagePicker.pickImage(
      source: source,
      imageQuality: 70,
    );
    if (!mounted || _submitting) return;
    if (picked != null) {
      setState(() {
        _resetRetry();
        _photo = picked;
      });
    }
  }

  Future<void> _submit() async {
    if (_submitting) return;
    // Validate the reading first.
    double? value;
    if (_isNumeric) {
      value = double.tryParse(_valueController.text.trim());
      if (value == null) {
        _snack(
          'Enter the ${widget.category.label.toLowerCase()} '
          'in ${widget.category.unit}.',
        );
        return;
      }
    }
    if (_position == null) {
      _snack('Waiting for location — please enable GPS and try again.');
      return;
    }

    final photo = _photo;
    final note = _noteController.text.trim();
    final condition = _condition;
    final position = _position!;
    final observedAt = DateTime.now().toUtc();
    setState(() => _submitting = true);
    try {
      if (!_session.signedIn) {
        await _session.signIn();
        if (!mounted) return;
        if (!_session.signedIn) {
          throw StateError('Sign in with a verified account to submit.');
        }
      }
      String? photoPath;
      if (photo != null && _retryReport == null) {
        final bytes = await photo.readAsBytes();
        final ext = photo.name.split('.').last;
        photoPath = await _repo.uploadPhoto(bytes, ext);
      }
      _retryReport ??= Report(
        category: widget.category,
        readingValue: _isNumeric ? value : null,
        readingUnit: _isNumeric ? widget.category.unit : null,
        condition: _isNumeric ? null : condition,
        note: note.isEmpty ? null : note,
        latitude: position.coordinates.latitude,
        longitude: position.coordinates.longitude,
        locationAccuracyM: position.accuracyM,
        observedAt: observedAt,
        photoPath: photoPath,
      );
      _retryKey ??= const Uuid().v4();
      await _repo.submit(_retryReport!, idempotencyKey: _retryKey);
      if (!mounted) return;
      _snack('Reading submitted for review — thank you!');
      Navigator.of(context).pop();
    } catch (e) {
      if (mounted) _snack('Could not submit: $e');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _snack(String msg) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: !_submitting,
      child: Scaffold(
        appBar: AppBar(
          title: Row(
            children: [
              ExcludeSemantics(
                child: Icon(
                  widget.category.icon,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              const SizedBox(width: 10),
              Text(widget.category.label),
            ],
          ),
        ),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // The reading — numeric value or plant condition.
            Text(
              widget.category.readingLabel,
              style: Theme.of(context).textTheme.labelLarge,
            ),
            const SizedBox(height: 8),
            if (_isNumeric)
              TextField(
                controller: _valueController,
                enabled: !_submitting,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                inputFormatters: [
                  FilteringTextInputFormatter.allow(RegExp(r'[0-9.\-]')),
                ],
                autofocus: true,
                decoration: InputDecoration(
                  hintText: 'e.g. 12.5',
                  suffixText: widget.category.unit,
                  border: const OutlineInputBorder(),
                ),
              )
            else
              SegmentedButton<Condition>(
                segments: const [
                  ButtonSegment(
                    value: Condition.normal,
                    label: Text('Normal'),
                    icon: Icon(
                      Icons.check_circle_outline,
                      color: AppTheme.success,
                    ),
                  ),
                  ButtonSegment(
                    value: Condition.warning,
                    label: Text('Warning'),
                    icon: Icon(
                      Icons.warning_amber_outlined,
                      color: AppTheme.warning,
                    ),
                  ),
                  ButtonSegment(
                    value: Condition.critical,
                    label: Text('Critical'),
                    icon: Icon(Icons.error_outline, color: AppTheme.danger),
                  ),
                ],
                selected: {_condition},
                onSelectionChanged: _submitting
                    ? null
                    : (s) => setState(() {
                        _resetRetry();
                        _condition = s.first;
                      }),
              ),
            const SizedBox(height: 16),

            ExpansionTile(
              title: const Text('Photo and note'),
              subtitle: ValueListenableBuilder<TextEditingValue>(
                valueListenable: _noteController,
                builder: (_, value, _) {
                  final details = [
                    if (_photo != null) 'Photo attached',
                    if (value.text.trim().isNotEmpty) 'Note added',
                  ];
                  return Text(
                    details.isEmpty
                        ? 'Optional supporting details'
                        : details.join(' · '),
                  );
                },
              ),
              tilePadding: EdgeInsets.zero,
              childrenPadding: const EdgeInsets.only(bottom: 16),
              maintainState: true,
              children: [
                // Photo
                if (_photo != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.file(
                        File(_photo!.path),
                        height: 180,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => const SizedBox(),
                      ),
                    ),
                  ),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _submitting
                            ? null
                            : () => _pickPhoto(ImageSource.camera),
                        icon: const Icon(Icons.photo_camera_outlined),
                        label: const Text('Camera'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _submitting
                            ? null
                            : () => _pickPhoto(ImageSource.gallery),
                        icon: const Icon(Icons.image_outlined),
                        label: const Text('Gallery'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Note
                TextField(
                  controller: _noteController,
                  enabled: !_submitting,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Note (optional)',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Location status
            Card(
              color: _locationError == null
                  ? AppTheme.soft
                  : Theme.of(context).colorScheme.errorContainer,
              child: ListTile(
                leading: Icon(
                  _locationError == null
                      ? Icons.location_on
                      : Icons.location_off,
                ),
                title: Text(
                  _locationError == null
                      ? (_position == null
                            ? 'Getting your location…'
                            : 'Location captured automatically')
                      : _locationError!,
                ),
                trailing: _locationError != null
                    ? TextButton(
                        onPressed: _submitting ? null : _captureLocation,
                        child: const Text('Retry'),
                      )
                    : null,
              ),
            ),
            const SizedBox(height: 16),

            const SizedBox(height: 24),

            FilledButton(
              onPressed: _submitting ? null : _submit,
              child: _submitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Submit reading'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _noteController.dispose();
    _valueController.dispose();
    super.dispose();
  }
}
