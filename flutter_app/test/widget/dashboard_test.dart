import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_app/features/teacher/dashboard/teacher_dashboard.dart';
import 'package:flutter_app/features/teacher/presentation/bloc/teacher_dashboard_bloc.dart';
import 'package:get_it/get_it.dart';

class MockTeacherDashboardBloc extends Mock implements TeacherDashboardBloc {}

void main() {
  late MockTeacherDashboardBloc mockBloc;

  setUpAll(() {
    final sl = GetIt.instance;
    mockBloc = MockTeacherDashboardBloc();
    sl.registerFactory<TeacherDashboardBloc>(() => mockBloc);
  });

  tearDownAll(() {
    GetIt.instance.reset();
  });

  testWidgets('TeacherDashboard shows Loading, Error, and Loaded states', (tester) async {
    // 1. Loading State
    when(() => mockBloc.state).thenReturn(TeacherDashboardLoading());
    when(() => mockBloc.stream).thenAnswer((_) => Stream.value(TeacherDashboardLoading()));

    await tester.pumpWidget(const MaterialApp(home: TeacherDashboard()));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    // 2. Error State
    when(() => mockBloc.state).thenReturn(TeacherDashboardError('Failed to load'));
    when(() => mockBloc.stream).thenAnswer((_) => Stream.value(TeacherDashboardError('Failed to load')));

    await tester.pump();
    expect(find.textContaining('Error: Failed to load'), findsOneWidget);

    // 3. Loaded State
    when(() => mockBloc.state).thenReturn(TeacherDashboardLoaded({}));
    when(() => mockBloc.stream).thenAnswer((_) => Stream.value(TeacherDashboardLoaded({})));

    await tester.pump();
    expect(find.text('AI Teacher - Faculty Panel'), findsOneWidget);
    expect(find.text('Verify Answers'), findsOneWidget);
  });
}
