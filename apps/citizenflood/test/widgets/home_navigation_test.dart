import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:citizenflood/services/depth_preview.dart';
import 'package:citizenflood/services/account_session.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/screens/home_shell.dart';

class CameraSession extends AccountSession {
  int version = 0;
  @override
  int get generation => version;
  void change() {
    version++;
    notifyListeners();
  }
}

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
  testWidgets('camera water opens directly and account changes close it', (
    tester,
  ) async {
    final calls = <MethodCall>[];
    final session = CameraSession();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(DepthPreview.channel, (call) async {
          calls.add(call);
          return null;
        });
    addTearDown(
      () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(DepthPreview.channel, null),
    );
    await tester.pumpWidget(MaterialApp(home: HomeShell(session: session)));
    await tester.pump();
    await tester.tap(find.byTooltip('Camera water'));
    await tester.pump();
    expect(calls.last.method, 'openCamera');
    expect(calls.last.arguments, isNull);
    session.change();
    await tester.pump();
    expect(calls.last.method, 'close');
  });
}
