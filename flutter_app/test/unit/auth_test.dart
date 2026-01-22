import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:dartz/dartz.dart';
import 'package:flutter_app/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:flutter_app/core/analytics/audit_logger.dart';
import 'package:flutter_app/features/auth/domain/usecases/login_usecase.dart';
import 'package:flutter_app/features/auth/domain/entities/user.dart';

class MockAuditLogger extends Mock implements AuditLogger {}
class MockLoginUseCase extends Mock implements LoginUseCase {}

void main() {
  late AuthBloc authBloc;
  late MockAuditLogger mockAuditLogger;
  late MockLoginUseCase mockLoginUseCase;

  setUp(() {
    mockAuditLogger = MockAuditLogger();
    mockLoginUseCase = MockLoginUseCase();
    authBloc = AuthBloc(loginUseCase: mockLoginUseCase, auditLogger: mockAuditLogger);
  });

  test('initial state should be AuthInitial', () {
    expect(authBloc.state, AuthInitial());
  });

  const tUser = User(id: '1', email: 'teacher@test.com', role: 'teacher');

  test('should emit [AuthLoading, AuthSuccess] when login is successful', () async {
    when(() => mockAuditLogger.logAction(any(), any())).thenAnswer((_) async {});
    when(() => mockLoginUseCase(any(), any())).thenAnswer((_) async => const Right(tUser));

    authBloc.add(LoginRequested('teacher@test.com', 'pass'));

    expectLater(authBloc.stream, emitsInOrder([
      AuthLoading(),
      const AuthSuccess(tUser),
    ]));
  });
}
