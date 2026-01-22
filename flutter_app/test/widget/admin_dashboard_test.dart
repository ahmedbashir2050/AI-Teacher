import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_app/features/admin/dashboard/admin_dashboard.dart';
import 'package:flutter_app/features/admin/presentation/bloc/admin_dashboard_bloc.dart';
import 'package:get_it/get_it.dart';

class MockAdminDashboardBloc extends Mock implements AdminDashboardBloc {}

void main() {
  late MockAdminDashboardBloc mockBloc;

  setUpAll(() {
    final sl = GetIt.instance;
    mockBloc = MockAdminDashboardBloc();
    sl.registerFactory<AdminDashboardBloc>(() => mockBloc);
  });

  tearDownAll(() {
    GetIt.instance.reset();
  });

  testWidgets('AdminDashboard displays system metrics and actions', (tester) async {
    when(() => mockBloc.state).thenReturn(AdminDashboardLoaded({}));
    when(() => mockBloc.stream).thenAnswer((_) => Stream.value(AdminDashboardLoaded({})));

    await tester.pumpWidget(const MaterialApp(home: AdminDashboard()));

    expect(find.text('System Administration'), findsOneWidget);
    expect(find.text('Students'), findsOneWidget);
    expect(find.text('RBAC Settings'), findsOneWidget);
    expect(find.text('Audit Explorer'), findsOneWidget);
  });
}
