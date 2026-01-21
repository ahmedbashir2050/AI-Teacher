import 'package:dio/dio.dart';
import '../../utils/logger.dart';

class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    AppLogger.d('REQUEST[${options.method}] => PATH: ${options.path}');
    AppLogger.d('HEADERS: ${options.headers}');
    AppLogger.d('BODY: ${options.data}');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    AppLogger.d('RESPONSE[${response.statusCode}] => PATH: ${response.requestOptions.path}');
    AppLogger.d('DATA: ${response.data}');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    AppLogger.e('ERROR[${err.response?.statusCode}] => PATH: ${err.requestOptions.path}');
    AppLogger.e('MESSAGE: ${err.message}');
    handler.next(err);
  }
}
