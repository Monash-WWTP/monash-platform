import 'dart:io';
import 'dart:ui' as ui;
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart' hide LocationSource;
import '../models/report.dart';
import 'map_selection.dart';

class CitizenMap extends StatefulWidget {
  static String markerImageKey(ReportCategory category, bool owner) =>
      '${owner ? 'own' : 'public'}-${category.wire}';
  const CitizenMap({
    super.key,
    required this.center,
    this.reports = const [],
    this.selectedId,
    this.onObservation,
    this.onCenterChanged,
    this.deviceLocation,
    this.resetKey = 0,
  });
  final SelectedLocation center;
  final SelectedLocation? deviceLocation;
  final List<Report> reports;
  final String? selectedId;
  final ValueChanged<Report>? onObservation;
  final ValueChanged<SelectedLocation>? onCenterChanged;
  final int resetKey;
  @override
  State<CitizenMap> createState() => _CitizenMapState();
}

class _CitizenMapState extends State<CitizenMap> {
  MapLibreMapController? _controller;
  bool _ready = false, _timedOut = false;
  Timer? _timer;
  int _revision = 0;
  int _attempt = 0;
  @override
  void initState() {
    super.initState();
    _timer = Timer(const Duration(seconds: 20), () {
      if (mounted && !_ready) setState(() => _timedOut = true);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _revision++;
    super.dispose();
  }

  @override
  void didUpdateWidget(CitizenMap old) {
    super.didUpdateWidget(old);
    if (_ready) {
      _draw();
      if (old.center != widget.center) {
        _controller?.animateCamera(
          CameraUpdate.newLatLng(
            LatLng(widget.center.latitude, widget.center.longitude),
          ),
        );
      }
    }
  }

  Future<void> _draw() async {
    final controller = _controller;
    if (controller == null || !_ready) return;
    final revision = ++_revision;
    await controller.setSymbolIconAllowOverlap(true);
    await controller.clearSymbols();
    await controller.clearCircles();
    if (!mounted || revision != _revision) return;
    for (final category in ReportCategory.values) {
      for (final owner in [true, false]) {
        final recorder = ui.PictureRecorder();
        final canvas = Canvas(recorder);
        canvas.drawCircle(
          const Offset(32, 32),
          29,
          Paint()..color = owner ? const Color(0xFF146346) : Colors.white,
        );
        canvas.drawCircle(
          const Offset(32, 32),
          29,
          Paint()
            ..color = owner ? Colors.white : const Color(0xFF146346)
            ..style = PaintingStyle.stroke
            ..strokeWidth = 3,
        );
        final icon = category.icon;
        final painter = TextPainter(
          text: TextSpan(
            text: String.fromCharCode(icon.codePoint),
            style: TextStyle(
              fontSize: 32,
              fontFamily: icon.fontFamily,
              package: icon.fontPackage,
              color: owner ? Colors.white : const Color(0xFF146346),
            ),
          ),
          textDirection: TextDirection.ltr,
        )..layout();
        painter.paint(
          canvas,
          Offset(32 - painter.width / 2, 32 - painter.height / 2),
        );
        final picture = recorder.endRecording();
        final image = await picture.toImage(64, 64);
        final data = await image.toByteData(format: ui.ImageByteFormat.png);
        image.dispose();
        picture.dispose();
        if (!mounted || revision != _revision) return;
        await controller.addImage(
          CitizenMap.markerImageKey(category, owner),
          data!.buffer.asUint8List(),
        );
      }
    }
    for (final report in widget.reports) {
      if (!mounted || revision != _revision) return;
      final point = LatLng(report.latitude, report.longitude);
      if (report.id == widget.selectedId) {
        await controller.addCircle(
          CircleOptions(
            geometry: point,
            circleRadius: 26,
            circleColor: '#146346',
            circleOpacity: 0.22,
            circleStrokeWidth: 2,
            circleStrokeColor: '#146346',
          ),
        );
      }
      await controller.addSymbol(
        SymbolOptions(
          geometry: point,
          iconImage: CitizenMap.markerImageKey(report.category, report.isOwner),
          iconSize: report.id == widget.selectedId ? 0.85 : 0.7,
        ),
        {'reportId': report.id},
      );
    }
    final location = widget.deviceLocation;
    if (location != null) {
      await controller.addCircle(
        CircleOptions(
          geometry: LatLng(location.latitude, location.longitude),
          circleRadius: 8,
          circleColor: '#2266B5',
          circleStrokeColor: '#FFFFFF',
          circleStrokeWidth: 3,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (Platform.environment.containsKey('FLUTTER_TEST')) {
      return ColoredBox(
        color: const Color(0xFFEAF0EC),
        child: Stack(
          children: [
            for (final report in widget.reports)
              Align(
                alignment: Alignment.center,
                child: Tooltip(
                  message: report.category.label,
                  child: IconButton(
                    onPressed: () => widget.onObservation?.call(report),
                    icon: Icon(report.category.icon),
                  ),
                ),
              ),
          ],
        ),
      );
    }
    return Stack(
      children: [
        MapLibreMap(
          key: ValueKey('${widget.resetKey}-$_attempt'),
          styleString: 'https://tiles.openfreemap.org/styles/liberty',
          initialCameraPosition: CameraPosition(
            target: LatLng(widget.center.latitude, widget.center.longitude),
            zoom: 13,
          ),
          trackCameraPosition: true,
          compassEnabled: true,
          rotateGesturesEnabled: false,
          tiltGesturesEnabled: false,
          onMapCreated: (controller) {
            _controller = controller;
            controller.onSymbolTapped.add((symbol) {
              final id = symbol.data?['reportId'];
              final report = widget.reports
                  .where((r) => r.id == id)
                  .firstOrNull;
              if (report != null) widget.onObservation?.call(report);
            });
          },
          onStyleLoadedCallback: () {
            _timer?.cancel();
            if (!mounted) return;
            setState(() {
              _ready = true;
              _timedOut = false;
            });
            _draw();
          },
          onCameraIdle: () {
            final target = _controller?.cameraPosition?.target;
            if (target != null) {
              widget.onCenterChanged?.call(
                SelectedLocation(
                  latitude: target.latitude,
                  longitude: target.longitude,
                  source: LocationSource.selected,
                ),
              );
            }
          },
        ),
        if (!_ready)
          Positioned(
            top: 12,
            left: 16,
            right: 16,
            child: Material(
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    if (!_timedOut)
                      const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _timedOut
                            ? 'Map unavailable. Check your connection.'
                            : 'Loading map…',
                      ),
                    ),
                    if (_timedOut)
                      TextButton(
                        onPressed: () => setState(() {
                          _timedOut = false;
                          _ready = false;
                          _attempt++;
                          _revision++;
                          _timer?.cancel();
                          _timer = Timer(const Duration(seconds: 20), () {
                            if (mounted && !_ready) {
                              setState(() => _timedOut = true);
                            }
                          });
                        }),
                        child: const Text('Retry'),
                      ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }
}
