import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';
import 'package:citizenflood/screens/report_form_screen.dart';
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

  testWidgets('all categories use distinct, accessible Material icons', (
    tester,
  ) async {
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
      expect(icon.semanticLabel, isNull);
      if (icon.icon != null) icons.add(icon.icon!);
    }
    expect(icons, hasLength(ReportCategory.values.length));
  });

  testWidgets('category tile exposes its visible category name once', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: CategoryTile(category: ReportCategory.rainfall, onTap: () {}),
        ),
      ),
    );

    expect(tester.getSemantics(find.byType(InkWell)).label, 'Rainfall');
    semantics.dispose();
  });

  test('AppTheme shares the landing page primary and neutral colors', () {
    final theme = AppTheme.light();

    expect(theme.colorScheme.primary, const Color(0xFF146346));
    expect(theme.colorScheme.onPrimary, Colors.white);
    expect(theme.colorScheme.surface, Colors.white);
    expect(theme.scaffoldBackgroundColor, Colors.white);
    expect(theme.colorScheme.onSurface, const Color(0xFF202724));
  });

  testWidgets(
    'plant condition severity icons use shared status colors and labels',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light(),
          home: const ReportFormScreen(category: ReportCategory.wastewater),
        ),
      );
      await tester.pump();

      expect(find.text('Normal'), findsOneWidget);
      expect(find.text('Warning'), findsOneWidget);
      expect(find.text('Critical'), findsOneWidget);
      final button = tester.widget<SegmentedButton<Condition>>(
        find.byType(SegmentedButton<Condition>),
      );
      final icons = {
        for (final segment in button.segments)
          segment.value: segment.icon! as Icon,
      };
      expect(icons[Condition.normal]!.color, AppTheme.green);
      expect(icons[Condition.warning]!.color, AppTheme.warning);
      expect(icons[Condition.critical]!.color, AppTheme.danger);
    },
  );
}
