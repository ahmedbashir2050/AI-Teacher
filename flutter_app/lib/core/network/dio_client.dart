import 'package:dio/dio.dart';
import '../config/env.dart';
import 'interceptors/auth_interceptor.dart';
import 'interceptors/logging_interceptor.dart';
import 'interceptors/retry_interceptor.dart';
import '../../security/token_manager.dart';

class DioClient {
  final Dio dio;
  final TokenManager tokenManager;

  DioClient(this.tokenManager) : dio = Dio() {
    dio
      ..options.baseUrl = Env.config.apiBaseUrl
      ..options.connectTimeout = const Duration(seconds: 30)
      ..options.receiveTimeout = const Duration(seconds: 30)
      ..options.headers = {'Content-Type': 'application/json'}
      ..interceptors.addAll([
        AuthInterceptor(tokenManager),
        LoggingInterceptor(),
        RetryInterceptor(dio: dio),
      ]);
  }

  Future<Response> get(String path, {Map<String, dynamic>? queryParameters, Options? options}) async {
    return await dio.get(path, queryParameters: queryParameters, options: options);
  }

  Future<Response> post(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return await dio.post(path, data: data, queryParameters: queryParameters, options: options);
  }

  Future<Response> put(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return await dio.put(path, data: data, queryParameters: queryParameters, options: options);
  }

  Future<Response> delete(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return await dio.delete(path, data: data, queryParameters: queryParameters, options: options);
  }
}
