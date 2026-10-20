import 'package:flutter/material.dart';
import '../models/report.dart';
import '../maps/map_selection.dart';
import 'report_form_screen.dart';

class CategoryScreen extends StatelessWidget {
  const CategoryScreen({super.key, this.selectedLocation, this.onShowReports});
  final VoidCallback? onShowReports;
  final SelectedLocation? selectedLocation;
  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(20),
    children: [
      if (selectedLocation != null) ...[
        Row(
          children: [
            Icon(
              Icons.place_outlined,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(width: 8),
            Expanded(child: Text(selectedLocation!.label)),
          ],
        ),
        const SizedBox(height: 28),
      ],
      Text(
        'What did you observe?',
        style: Theme.of(context).textTheme.headlineSmall,
      ),
      const SizedBox(height: 20),
      for (final category in ReportCategory.values) ...[
        ListTile(
          contentPadding: const EdgeInsets.symmetric(
            vertical: 14,
            horizontal: 8,
          ),
          leading: Icon(
            category.icon,
            size: 28,
            color: Theme.of(context).colorScheme.primary,
          ),
          title: Text(category.label),
          subtitle: Text(
            category.isNumeric ? category.unit : 'Plant condition',
          ),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ReportFormScreen(
                onShowReports: onShowReports,
                category: category,
                selectedLocation: selectedLocation,
              ),
            ),
          ),
        ),
        const Divider(height: 1),
      ],
    ],
  );
}
