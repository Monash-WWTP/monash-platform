import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:citizenflood/screens/my_reports_screen.dart';
import 'package:citizenflood/services/report_repository.dart';
import 'package:citizenflood/services/account_session.dart';
import 'package:citizenflood/models/report.dart';

class Session extends AccountSession {
  bool active = true;
  int revision = 0;
  @override
  bool get signedIn => active;
  @override
  int get generation => revision;
  void logout() {
    active = false;
    revision++;
    notifyListeners();
  }
}

class Repository extends ReportRepository {
  final read = Completer<ReportPage>();
  @override
  Future<ReportPage> own({int limit = 25, int offset = 0}) => read.future;
}

class CountingRepository extends ReportRepository {int calls=0;@override Future<ReportPage> own({int limit=25,int offset=0})async{calls++;return ReportPage(items:[],total:0,offset:offset,limit:limit);}}
void main() {
 testWidgets('entering reports again reloads same-account submissions',(t)async{
   final s=Session();final r=CountingRepository();
   Widget app(bool active)=>MaterialApp(home:Scaffold(body:MyReportsScreen(session:s,repository:r,active:active)));
   await t.pumpWidget(app(false));await t.pumpAndSettle();expect(r.calls,0);
   await t.pumpWidget(app(true));await t.pumpAndSettle();expect(r.calls,1);
   await t.pumpWidget(app(false));await t.pumpWidget(app(true));await t.pumpAndSettle();expect(r.calls,2);
 });

  testWidgets('late private history is discarded after logout', (t) async {
    final s = Session(), r = Repository();
    await t.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MyReportsScreen(session: s, repository: r),
        ),
      ),
    );
    s.logout();
    await t.pump();
    r.read.complete(
      ReportPage(
        items: [
          Report(
            id: 'private',
            category: ReportCategory.rainfall,
            latitude: 3,
            longitude: 101,
            note: 'private note',
            readingValue: 12,
          ),
        ],
        total: 1,
        offset: 0,
        limit: 25,
      ),
    );
    await t.pumpAndSettle();
    expect(find.text('Rainfall'), findsNothing);
    expect(find.text('private note'), findsNothing);
    expect(find.text('Sign in'), findsOneWidget);
  });
}
