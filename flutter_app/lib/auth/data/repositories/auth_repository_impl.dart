import 'package:dartz/dartz.dart';
import '../../domain/repositories/auth_repository.dart';
import '../../domain/entities/user.dart';
import '../models/user_model.dart';
import '../datasources/auth_remote_ds.dart';
import '../datasources/auth_local_ds.dart';
import '../../../core/error/failure.dart';
import '../../../core/network/network_info.dart';
import '../../../core/error/error_mapper.dart';
import '../../../core/security/token_manager.dart';
import 'package:get/get.dart';

class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource remoteDataSource;
  final AuthLocalDataSource localDataSource;
  final NetworkInfo networkInfo;

  AuthRepositoryImpl({
    required this.remoteDataSource,
    required this.localDataSource,
    required this.networkInfo,
  });

  @override
  Future<Either<Failure, User>> loginEmail(String email, String password) async {
    if (await networkInfo.isConnected) {
      try {
        final data = await remoteDataSource.loginEmail(email, password);
        final user = UserModel.fromJson(data['user']);
        await localDataSource.cacheUser(user);

        final tokenManager = Get.find<TokenManager>();
        await tokenManager.saveTokens(
          access: data['access_token'],
          refresh: data['refresh_token'],
        );

        return Right(user);
      } catch (e) {
        return Left(ErrorMapper.mapExceptionToFailure(e));
      }
    } else {
      return const Left(NetworkFailure('No internet connection'));
    }
  }

  @override
  Future<Either<Failure, User>> loginGoogle(String idToken) async {
    if (await networkInfo.isConnected) {
      try {
        final data = await remoteDataSource.loginGoogle(idToken);
        final user = UserModel.fromJson(data['user']);
        await localDataSource.cacheUser(user);

        final tokenManager = Get.find<TokenManager>();
        await tokenManager.saveTokens(
          access: data['access_token'],
          refresh: data['refresh_token'],
        );

        return Right(user);
      } catch (e) {
        return Left(ErrorMapper.mapExceptionToFailure(e));
      }
    } else {
      return const Left(NetworkFailure('No internet connection'));
    }
  }

  @override
  Future<Either<Failure, void>> logout() async {
    try {
      await remoteDataSource.logout();
      await localDataSource.clearCache();
      await Get.find<TokenManager>().deleteTokens();
      return const Right(null);
    } catch (e) {
      return Left(ErrorMapper.mapExceptionToFailure(e));
    }
  }

  @override
  Future<Either<Failure, String>> refreshToken(String refreshToken) async {
    // Implement refresh logic
    return const Left(ServerFailure('Not implemented'));
  }

  @override
  Future<Either<Failure, User?>> getAuthenticatedUser() async {
    try {
      final user = await localDataSource.getCachedUser();
      return Right(user);
    } catch (e) {
      return Left(ErrorMapper.mapExceptionToFailure(e));
    }
  }
}
