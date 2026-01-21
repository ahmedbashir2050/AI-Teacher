import 'package:get/get.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/config/api_endpoints.dart';
import '../../../../core/utils/logger.dart';

class AdminDashboardController extends GetxController {
  final DioClient dioClient;

  AdminDashboardController({required this.dioClient});

  final _isLoading = false.obs;
  bool get isLoading => _isLoading.value;

  Future<void> approveCurriculum(String curriculumId) async {
    _isLoading.value = true;
    try {
      await dioClient.post('${ApiEndpoints.curriculumApprove}/$curriculumId/approve');
      Get.snackbar('Success', 'Curriculum approved');
    } catch (e) {
      AppLogger.e('Failed to approve curriculum: $e');
      Get.snackbar('Error', 'Approval failed');
    } finally {
      _isLoading.value = false;
    }
  }

  Future<void> reindexRAG() async {
    // Call RAG reindexing endpoint
    Get.snackbar('Info', 'RAG Reindexing started');
  }
}
