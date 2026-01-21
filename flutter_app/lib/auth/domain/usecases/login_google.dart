import 'package:dartz/dartz.dart';
import '../../../core/error/failure.dart';
import '../entities/user.dart';
import '../repositories/auth_repository.dart';

class LoginGoogle {
  final AuthRepository repository;

  LoginGoogle(this.repository);

  Future<Either<Failure, User>> call(String idToken) async {
    return await repository.loginGoogle(idToken);
  }
}
