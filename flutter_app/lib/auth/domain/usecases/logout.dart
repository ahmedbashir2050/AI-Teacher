import 'package:dartz/dartz.dart';
import '../../../core/error/failure.dart';
import '../repositories/auth_repository.dart';

class Logout {
  final AuthRepository repository;

  Logout(this.repository);

  Future<Either<Failure, void>> call() async {
    return await repository.logout();
  }
}
