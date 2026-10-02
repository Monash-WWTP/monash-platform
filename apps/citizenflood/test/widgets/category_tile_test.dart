import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/models/report.dart';
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
}
