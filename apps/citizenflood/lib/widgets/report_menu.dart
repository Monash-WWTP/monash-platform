import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../models/report.dart';

class ReportMenu extends StatefulWidget {
  const ReportMenu({super.key, required this.onSelected});
  final ValueChanged<ReportCategory> onSelected;
  @override
  State<ReportMenu> createState() => _ReportMenuState();
}

class _ReportMenuState extends State<ReportMenu> {
  final _anchor = GlobalKey();
  bool _open = false;
  Future<void> _show() async {
    if (_open) return;
    final box = _anchor.currentContext!.findRenderObject() as RenderBox;
    final origin = box.localToGlobal(Offset.zero);
    final size = MediaQuery.sizeOf(context);
    final right = math.max(12.0, size.width - origin.dx - box.size.width);
    final colors = Theme.of(context).colorScheme;
    setState(() => _open = true);
    final result = await showGeneralDialog<ReportCategory>(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'Dismiss report menu',
      barrierColor: Colors.black.withValues(alpha: .16),
      transitionDuration: MediaQuery.disableAnimationsOf(context)
          ? Duration.zero
          : const Duration(milliseconds: 160),
      transitionBuilder: (c, animation, secondary, child) => FadeTransition(
        opacity: animation,
        child: SlideTransition(
          position: Tween(begin: const Offset(0, .025), end: Offset.zero)
              .animate(
                CurvedAnimation(parent: animation, curve: Curves.easeOutCubic),
              ),
          child: child,
        ),
      ),
      pageBuilder: (c, animation, secondary) => LayoutBuilder(
        builder: (c, constraints) {
          final viewport = Size(constraints.maxWidth, constraints.maxHeight);
          final padding = MediaQuery.paddingOf(c);
          final top = origin.dy
              .clamp(
                padding.top + 12,
                math.max(
                  padding.top + 12,
                  viewport.height - padding.bottom - 68,
                ),
              )
              .toDouble();
          final available = math.max(48.0, top - padding.top - 24);
          return Stack(
            children: [
              Positioned(
                right: right,
                bottom: viewport.height - top + 12,
                width: math.min(340, viewport.width - right - 12),
                child: ConstrainedBox(
                  constraints: BoxConstraints(maxHeight: available),
                  child: SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        for (final item
                            in const <(ReportCategory, String, IconData)>[
                              (
                                ReportCategory.waterLevel,
                                'Flooding',
                                Icons.flood_outlined,
                              ),
                              (
                                ReportCategory.rainfall,
                                'Rain',
                                Icons.umbrella_outlined,
                              ),
                              (
                                ReportCategory.wastewater,
                                'Water appearance',
                                Icons.water_outlined,
                              ),
                              (
                                ReportCategory.temperature,
                                'Add measurement',
                                Icons.straighten,
                              ),
                            ])
                          Padding(
                            padding: const EdgeInsets.only(top: 12),
                            child: Semantics(
                              button: true,
                              onTap: () => Navigator.pop(c, item.$1),
                              label: item.$2,
                              child: ExcludeSemantics(
                                child: Material(
                                  color: Colors.transparent,
                                  child: InkWell(
                                    borderRadius: BorderRadius.circular(24),
                                    onTap: () => Navigator.pop(c, item.$1),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Flexible(
                                          child: Material(
                                            color: colors.surface,
                                            elevation: 2,
                                            borderRadius: BorderRadius.circular(
                                              20,
                                            ),
                                            child: Padding(
                                              padding:
                                                  const EdgeInsets.symmetric(
                                                    horizontal: 16,
                                                    vertical: 10,
                                                  ),
                                              child: Text(
                                                item.$2,
                                                style: TextStyle(
                                                  color: colors.onSurface,
                                                  fontSize: 16,
                                                ),
                                              ),
                                            ),
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                        Material(
                                          color: colors.surface,
                                          elevation: 3,
                                          shape: const CircleBorder(),
                                          child: SizedBox(
                                            width: 48,
                                            height: 48,
                                            child: Icon(
                                              item.$3,
                                              color: colors.primary,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
              Positioned(
                top: top,
                right: right,
                child: FloatingActionButton(
                  heroTag: null,
                  shape: const CircleBorder(),
                  tooltip: 'Close report menu',
                  onPressed: () => Navigator.pop(c),
                  child: const Icon(Icons.close),
                ),
              ),
            ],
          );
        },
      ),
    );
    if (!mounted) return;
    setState(() => _open = false);
    if (result != null) widget.onSelected(result);
  }

  @override
  Widget build(BuildContext context) => SizedBox(
    key: _anchor,
    width: 56,
    height: 56,
    child: FloatingActionButton(
      heroTag: 'new-report',
      shape: const CircleBorder(),
      tooltip: 'New report',
      onPressed: _show,
      child: const Icon(Icons.add, size: 28),
    ),
  );
}
