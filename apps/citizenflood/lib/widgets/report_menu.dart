import 'package:flutter/material.dart';
import '../models/report.dart';

class ReportMenu extends StatelessWidget {
  const ReportMenu({super.key, required this.onSelected});
  final ValueChanged<ReportCategory> onSelected;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return PopupMenuButton<ReportCategory>(
      tooltip: 'New report',
      icon: const Icon(Icons.add),
      iconSize: 28,
      position: PopupMenuPosition.over,
      offset: const Offset(0, -232),
      popUpAnimationStyle: MediaQuery.disableAnimationsOf(context)
          ? AnimationStyle.noAnimation
          : const AnimationStyle(duration: Duration(milliseconds: 160)),
      style: ButtonStyle(
        backgroundColor: WidgetStatePropertyAll(colors.primary),
        foregroundColor: WidgetStatePropertyAll(colors.onPrimary),
        fixedSize: const WidgetStatePropertyAll(Size(56, 56)),
        shape: const WidgetStatePropertyAll(CircleBorder()),
        elevation: const WidgetStatePropertyAll(3),
      ),
      onSelected: onSelected,
      itemBuilder: (_) => [
        for (final category in ReportCategory.values)
          PopupMenuItem(
            value: category,
            height: 56,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                children: [
                  Icon(category.icon, color: colors.primary),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      category == ReportCategory.wastewater
                          ? 'Plant condition'
                          : category.label,
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}
