import '../../core/network/dio_client.dart';
import 'package:get/get.dart';

class AuditService {
  final DioClient dioClient = Get.find<DioClient>();

  Future<void> logAction(String action, Map<String, dynamic> metadata) async {
    try {
      await dioClient.post('/audit/log', data: {
        'action': action,
        'metadata': metadata,
        'timestamp': DateTime.now().toIso8601String(),
      });
    } catch (e) {
      // Fail silently or cache for later retry
    }
  }
}
