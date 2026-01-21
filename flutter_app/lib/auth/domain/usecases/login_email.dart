import 'package:dartz/dartz.dart';
import '../../../core/error/failure.dart';
import '../entities/user.dart';
import '../repositories/auth_repository.dart';

class LoginEmail {
  final AuthRepository repository;

  LoginEmail(this.repository);

  Future<Either<Failure, User>> call(String email, String password) async {
    return await repository.loginEmail(email, password);
  }
}
