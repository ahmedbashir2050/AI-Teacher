import 'package:dio/dio.dart';
import 'audit_service.dart';

class AuditInterceptor extends Interceptor {
  final AuditService _auditService;

  AuditInterceptor(this._auditService);

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    if (response.requestOptions.method != 'GET') {
      _auditService.logAction('API_WRITE_SUCCESS', {
        'path': response.requestOptions.path,
        'method': response.requestOptions.method,
        'status': response.statusCode,
      });
    }
    handler.next(response);
  }
}
