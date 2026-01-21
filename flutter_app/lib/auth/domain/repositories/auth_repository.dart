import 'package:dartz/dartz.dart';
import '../../../core/error/failure.dart';
import '../entities/user.dart';

abstract class AuthRepository {
  Future<Either<Failure, User>> loginEmail(String email, String password);
  Future<Either<Failure, User>> loginGoogle(String idToken);
  Future<Either<Failure, void>> logout();
  Future<Either<Failure, String>> refreshToken(String refreshToken);
  Future<Either<Failure, User?>> getAuthenticatedUser();
}
