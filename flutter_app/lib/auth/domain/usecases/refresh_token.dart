import 'package:dartz/dartz.dart';
import '../../../core/error/failure.dart';
import '../repositories/auth_repository.dart';

class RefreshToken {
  final AuthRepository repository;

  RefreshToken(this.repository);

  Future<Either<Failure, String>> call(String refreshToken) async {
    return await repository.refreshToken(refreshToken);
  }
}
