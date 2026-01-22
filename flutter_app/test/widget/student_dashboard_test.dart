import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_app/features/student/dashboard/student_dashboard.dart';
import 'package:flutter_app/features/student/presentation/bloc/student_dashboard_bloc.dart';
import 'package:get_it/get_it.dart';

class MockStudentDashboardBloc extends Mock implements StudentDashboardBloc {}

void main() {
  late MockStudentDashboardBloc mockBloc;

  setUpAll(() {
    final sl = GetIt.instance;
    mockBloc = MockStudentDashboardBloc();
    sl.registerFactory<StudentDashboardBloc>(() => mockBloc);
  });

  tearDownAll(() {
    GetIt.instance.reset();
  });

  testWidgets('StudentDashboard displays main feature cards', (tester) async {
    when(() => mockBloc.state).thenReturn(StudentDashboardLoaded({}, []));
    when(() => mockBloc.stream).thenAnswer((_) => Stream.value(StudentDashboardLoaded({}, [])));

    await tester.pumpWidget(const MaterialApp(home: StudentDashboard()));

    expect(find.text('Student Dashboard'), findsOneWidget);
    expect(find.text('Ask AI'), findsOneWidget);
    expect(find.text('Exams'), findsOneWidget);
    expect(find.text('Progress'), findsOneWidget);
  });
}
