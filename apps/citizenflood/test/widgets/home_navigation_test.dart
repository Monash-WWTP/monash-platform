import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/screens/home_shell.dart';

void main() {
  testWidgets('map first with report history and account destinations', (
    tester,
  ) async {
    await tester.pumpWidget(const MaterialApp(home: HomeShell()));
    await tester.pump();
    final nav = tester.widget<NavigationBar>(find.byType(NavigationBar));
    expect(nav.selectedIndex, 0);
    expect(find.text('My reports'), findsOneWidget);
    expect(find.text('Account'), findsOneWidget);
    expect(find.byTooltip('New report'), findsOneWidget);
  });
}
