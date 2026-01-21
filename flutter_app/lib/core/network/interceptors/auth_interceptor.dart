import 'package:dio/dio.dart';
import '../../security/token_manager.dart';

class AuthInterceptor extends Interceptor {
  final TokenManager _tokenManager;

  AuthInterceptor(this._tokenManager);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _tokenManager.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    // Inject required headers for microservices
    final facultyId = await _tokenManager.getFacultyId();
    if (facultyId != null) {
      options.headers['X-User-Faculty-Id'] = facultyId;
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Logic for token refresh would go here
      // For now, just pass the error
    }
    handler.next(err);
  }
}
