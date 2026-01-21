import 'failure.dart';
import 'exceptions.dart';
import '../constants/app_strings.dart';

class ErrorMapper {
  static Failure mapExceptionToFailure(Object exception) {
    if (exception is ServerException) {
      return ServerFailure(exception.message);
    } else if (exception is AuthException) {
      return AuthFailure(exception.message);
    } else if (exception is CacheException) {
      return const CacheFailure('Cache Error');
    } else {
      return const ServerFailure(AppStrings.errorGeneric);
    }
  }
}
