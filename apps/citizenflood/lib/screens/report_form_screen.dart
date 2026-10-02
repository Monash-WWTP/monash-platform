import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import '../models/report.dart';
import '../services/location_service.dart';
import '../services/report_repository.dart';
import '../services/account_session.dart';
import 'package:uuid/uuid.dart';

class ReportFormScreen extends StatefulWidget {
  const ReportFormScreen({super.key, required this.category});
  final ReportCategory category;

  @override
  State<ReportFormScreen> createState() => _ReportFormScreenState();
}

class _ReportFormScreenState extends State<ReportFormScreen> {
  final _location = LocationService();
  final _repo = ReportRepository();
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
    _captureLocation();
  }

  Future<void> _captureLocation() async {
    try {
      final pos = await _location.current();
      if (!mounted) return;
      setState(() {
        _position = pos;
        _locationError = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _locationError = e.toString());
    }
  }

  Future<void> _pickPhoto(ImageSource source) async {
    final picked = await ImagePicker().pickImage(
      source: source,
      imageQuality: 70,
    );
    if (!mounted) return;
    if (picked != null) setState(() => _photo = picked);
  }

  Future<void> _submit() async {
    if (!AccountSession.instance.signedIn) {
      try { await AccountSession.instance.signIn(); } catch (_) { _snack('Sign in with a verified account to submit.'); return; }
    }
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

    setState(() => _submitting = true);
    try {
      String? photoPath;
      if (_photo != null) {
        final bytes = await _photo!.readAsBytes();
        final ext = _photo!.name.split('.').last;
        photoPath = await _repo.uploadPhoto(bytes, ext);
      }
      _retryReport ??= Report(
          category: widget.category,
          readingValue: _isNumeric ? value : null,
          readingUnit: _isNumeric ? widget.category.unit : null,
          condition: _isNumeric ? null : _condition,
          note: _noteController.text.trim().isEmpty
              ? null
              : _noteController.text.trim(),
          latitude: _position!.coordinates.latitude,
          longitude: _position!.coordinates.longitude,
          locationAccuracyM: _position!.accuracyM,
          observedAt: DateTime.now().toUtc(),
          photoPath: photoPath,
        );
      _retryKey ??= const Uuid().v4();
      await _repo.submit(_retryReport!, idempotencyKey: _retryKey);
      if (!mounted) return;
      _snack('Reading submitted for review — thank you!');
      Navigator.of(context).pop();
    } catch (e) {
      _snack('Could not submit: $e');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _snack(String msg) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.category.emoji} ${widget.category.label}'),
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
                  icon: Icon(Icons.check_circle_outline),
                ),
                ButtonSegment(
                  value: Condition.warning,
                  label: Text('Warning'),
                  icon: Icon(Icons.warning_amber_outlined),
                ),
                ButtonSegment(
                  value: Condition.critical,
                  label: Text('Critical'),
                  icon: Icon(Icons.error_outline),
                ),
              ],
              selected: {_condition},
              onSelectionChanged: (s) => setState(() => _condition = s.first),
            ),
          const SizedBox(height: 16),

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
                  onPressed: () => _pickPhoto(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: const Text('Camera'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _pickPhoto(ImageSource.gallery),
                  icon: const Icon(Icons.image_outlined),
                  label: const Text('Gallery'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Location status
          Card(
            color: _locationError == null
                ? const Color(0xFFEAFAF2)
                : const Color(0xFFFDECEA),
            child: ListTile(
              leading: Icon(
                _locationError == null ? Icons.location_on : Icons.location_off,
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
                      onPressed: _captureLocation,
                      child: const Text('Retry'),
                    )
                  : null,
            ),
          ),
          const SizedBox(height: 16),

          // Note
          TextField(
            controller: _noteController,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Note (optional)',
              border: OutlineInputBorder(),
            ),
          ),
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
    );
  }

  @override
  void dispose() {
    _noteController.dispose();
    _valueController.dispose();
    super.dispose();
  }
}
