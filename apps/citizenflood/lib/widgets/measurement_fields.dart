import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/depth_preview.dart';
import '../screens/depth_preview_screen.dart';

class MeasurementFields extends StatefulWidget {
  const MeasurementFields({
    super.key,
    required this.kind,
    required this.references,
    required this.onChanged,
  });
  final String kind;
  final List<Map<String, dynamic>> references;
  final VoidCallback onChanged;
  @override
  State<MeasurementFields> createState() => MeasurementFieldsState();
}

class MeasurementFieldsState extends State<MeasurementFields> {
  final _fields = <String, TextEditingController>{};
  String _amount = 'value',
      _reference = 'depth',
      _method = 'instrument',
      _subject = 'water',
      _calibration = 'unknown';
  String? _station;
  DateTime? _start, _end;
  String? _error;
  TextEditingController field(String k) =>
      _fields.putIfAbsent(k, () => TextEditingController());
  @override
  void dispose() {
    for (final c in _fields.values) {
      c.dispose();
    }
    super.dispose();
  }

  Widget text(
    String k,
    String label, {
    bool numeric = false,
    bool required = true,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: TextFormField(
      controller: field(k),
      decoration: InputDecoration(labelText: label),
      keyboardType: numeric
          ? const TextInputType.numberWithOptions(decimal: true, signed: true)
          : TextInputType.text,
      onChanged: (_) {
        setState(() {});
        widget.onChanged();
      },
      validator: (v) {
        if (required && (v?.trim().isEmpty ?? true)) return 'Required';
        if (numeric && v != null && v.isNotEmpty) {
          final n = double.tryParse(v);
          if (n == null || !n.isFinite) return 'Enter a finite number';
        }
        return null;
      },
    ),
  );
  Widget choice(
    String label,
    String value,
    List<(String, String)> items,
    ValueChanged<String> change,
  ) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: DropdownButtonFormField<String>(
      initialValue: value,
      isExpanded: true,
      decoration: InputDecoration(labelText: label),
      items: [
        for (final i in items) DropdownMenuItem(value: i.$1, child: Text(i.$2)),
      ],
      onChanged: (v) {
        if (v != null) {
          setState(() => change(v));
          widget.onChanged();
        }
      },
    ),
  );
  Future<void> date(bool start) async {
    final now = DateTime.now();
    final initial = (start ? _start : _end) ?? now;
    final day = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2000),
      lastDate: now,
    );
    if (day == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(initial),
    );
    if (time == null || !mounted) return;
    setState(() {
      final d = DateTime(day.year, day.month, day.day, time.hour, time.minute);
      if (start) {
        _start = d;
      } else {
        _end = d;
      }
    });
    widget.onChanged();
  }

  Map<String, dynamic>? observation() {
    final k = widget.kind;
    final d = <String, dynamic>{'kind': k, 'method': 'instrument'};
    String value(String key) => field(key).text.trim();
    String? error;
    if (k == 'rainfall_accumulation') {
      final n = _amount == 'value' ? double.tryParse(value('value')) : null;
      if (_start == null || _end == null || !_start!.isBefore(_end!)) {
        error = 'Choose the collection start and end times.';
      }
      if (n != null && n < 0) error = 'Rainfall cannot be negative.';
      d.addAll({
        'amount_state': _amount,
        'value': n,
        'unit': 'mm',
        'interval_start': _start?.toUtc().toIso8601String(),
        'interval_end': _end?.toUtc().toIso8601String(),
        'gauge_type': value('gauge_type'),
        'gauge_id': value('gauge_id'),
      });
    } else if (k == 'water_reading') {
      final n = double.tryParse(value('value'));
      if (_reference == 'depth' && n != null && n < 0) {
        error = 'Depth cannot be negative.';
      }
      d.addAll({
        'method': _method,
        'value': n,
        'unit': 'm',
        'reference_kind': _reference,
        'instrument': _method == 'instrument' ? value('instrument') : null,
      });
      if (_reference == 'depth') {
        d['reference_description'] = value('surface');
      } else {
        final ref = widget.references
            .where((r) => r['id'] == _station)
            .firstOrNull;
        if (ref == null) {
          error = 'Choose an approved gauge reference.';
        } else {
          d['reference_id'] = ref['id'];
          d['reference_revision'] = ref['revision'];
        }
      }
    } else {
      final n = double.tryParse(value('value'));
      if (n != null && n < -273.15) {
        error = 'Temperature is below absolute zero.';
      }
      d.addAll({
        'value': n,
        'unit': '°C',
        'subject': _subject,
        'instrument': value('instrument'),
        'sample_context': value('sample_context'),
        'calibration_status': _calibration,
        'calibration_note': _calibration == 'known'
            ? value('calibration_note')
            : null,
      });
    }
    setState(() => _error = error);
    return error == null ? d : null;
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      const Padding(
        padding: EdgeInsets.only(bottom: 16),
        child: Text(
          'Record an existing reading from a safe position. Do not enter floodwater or collect wastewater.',
        ),
      ),
      if (widget.kind == 'rainfall_accumulation') ...[
        choice('Gauge result', _amount, const [
          ('value', 'Amount'),
          ('trace', 'Trace'),
          ('missing', 'Missing'),
        ], (v) => _amount = v),
        if (_amount == 'value')
          text('value', 'Accumulated rainfall (mm)', numeric: true),
        OutlinedButton(
          onPressed: () => date(true),
          child: Text(
            _start == null
                ? 'Collection start'
                : DateFormat('d MMM y · HH:mm').format(_start!),
          ),
        ),
        OutlinedButton(
          onPressed: () => date(false),
          child: Text(
            _end == null
                ? 'Collection end'
                : DateFormat('d MMM y · HH:mm').format(_end!),
          ),
        ),
        const SizedBox(height: 16),
        text('gauge_type', 'Gauge type'),
        text('gauge_id', 'Gauge or site identifier'),
      ] else if (widget.kind == 'water_reading') ...[
        choice(
          'Reading',
          _reference,
          const [('depth', 'Depth above a surface'), ('stage', 'Gauge stage')],
          (v) {
            _reference = v;
            if (v == 'stage') _method = 'instrument';
          },
        ),
        if (_reference == 'depth') ...[
          choice('Method', _method, const [
            ('instrument', 'Instrument reading'),
            ('estimate', 'Estimate'),
          ], (v) => _method = v),
          text('surface', 'Reference surface (for example road surface)'),
        ] else if (widget.references.isEmpty)
          const Padding(
            padding: EdgeInsets.only(bottom: 16),
            child: Text(
              'No approved gauge references are available. Use a described depth reference instead.',
            ),
          )
        else
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: DropdownButtonFormField<String>(
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Approved gauge'),
              items: [
                for (final r in widget.references)
                  DropdownMenuItem(
                    value: r['id'] as String,
                    child: Text('${r['label']} · revision ${r['revision']}'),
                  ),
              ],
              onChanged: (v) {
                setState(() => _station = v);
                widget.onChanged();
              },
              validator: (v) => v == null ? 'Choose a reference' : null,
            ),
          ),
        text(
          'value',
          _reference == 'depth' ? 'Depth (m)' : 'Stage (m)',
          numeric: true,
        ),
        if (_method == 'instrument') text('instrument', 'Instrument or gauge'),
        if (_reference == 'depth')
          Builder(
            builder: (context) {
              final preview = DepthPreview.fromObservation({
                'kind': 'water_reading',
                'reference_kind': _reference,
                'unit': 'm',
                'value': double.tryParse(field('value').text.trim()),
                'reference_description': field('surface').text,
              });
              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: OutlinedButton.icon(
                  onPressed: preview == null
                      ? null
                      : () => Navigator.push(
                          context,
                          MaterialPageRoute<void>(
                            builder: (_) => DepthPreviewScreen(
                              preview: preview,
                              contextLabel: 'Draft depth',
                            ),
                          ),
                        ),
                  icon: const Icon(Icons.view_in_ar),
                  label: const Text('Preview depth'),
                ),
              );
            },
          ),
      ] else ...[
        choice('Temperature subject', _subject, const [
          ('water', 'Water'),
          ('air', 'Air'),
        ], (v) => _subject = v),
        text('value', 'Temperature (°C)', numeric: true),
        text('instrument', 'Thermometer or probe'),
        text('sample_context', 'Sampling position or depth'),
        choice('Calibration provenance', _calibration, const [
          ('unknown', 'Unknown'),
          ('known', 'Known'),
        ], (v) => _calibration = v),
        if (_calibration == 'known')
          text('calibration_note', 'Calibration source or record'),
      ],
      if (_error != null)
        Text(
          _error!,
          style: TextStyle(color: Theme.of(context).colorScheme.error),
        ),
    ],
  );
}
