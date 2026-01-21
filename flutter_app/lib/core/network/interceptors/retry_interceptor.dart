import 'package:dio/dio.dart';
import 'dart:io';

class RetryInterceptor extends Interceptor {
  final Dio dio;
  final int maxRetries;
  final int retryDelayMs;

  RetryInterceptor({
    required this.dio,
    this.maxRetries = 3,
    this.retryDelayMs = 1000,
  });

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    var requestOptions = err.requestOptions;

    if (_shouldRetry(err)) {
      int attempt = (requestOptions.extra['retry_attempt'] ?? 0) + 1;

      if (attempt <= maxRetries) {
        requestOptions.extra['retry_attempt'] = attempt;
        await Future.delayed(Duration(milliseconds: retryDelayMs));

        try {
          final response = await dio.fetch(requestOptions);
          return handler.resolve(response);
        } catch (e) {
          return handler.next(err);
        }
      }
    }

    handler.next(err);
  }

  bool _shouldRetry(DioException err) {
    return err.type != DioExceptionType.cancel &&
           err.error is SocketException;
  }
}
