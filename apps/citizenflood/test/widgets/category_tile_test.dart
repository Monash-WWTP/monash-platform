import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/theme/app_theme.dart';
import 'package:citizenflood/widgets/category_tile.dart';

void main() {
  testWidgets('CategoryTile shows label and fires onTap', (tester) async {
    var tapped = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: CategoryTile(
            category: ReportCategory.rainfall,
            onTap: () => tapped = true,
          ),
        ),
      ),
    );

    expect(find.text('Rainfall'), findsOneWidget);
    await tester.tap(find.byType(CategoryTile));
    expect(tapped, isTrue);
  });

  testWidgets('all categories use distinct, accessible Material icons', (tester) async {
    final icons = <IconData>{};
    for (final category in ReportCategory.values) {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CategoryTile(category: category, onTap: () {}),
          ),
        ),
      );

      final iconFinder = find.byType(Icon);
      expect(iconFinder, findsOneWidget, reason: category.label);
      final icon = tester.widget<Icon>(iconFinder);
      expect(icon.semanticLabel, category.label);
      if (icon.icon != null) icons.add(icon.icon!);
    }
    expect(icons, hasLength(ReportCategory.values.length));
  });

  test('AppTheme shares the landing page primary and neutral colors', () {
    final theme = AppTheme.light();

    expect(theme.colorScheme.primary, const Color(0xFF146346));
    expect(theme.colorScheme.onPrimary, Colors.white);
    expect(theme.colorScheme.surface, Colors.white);
    expect(theme.scaffoldBackgroundColor, Colors.white);
    expect(theme.colorScheme.onSurface, const Color(0xFF202724));
  });
}
