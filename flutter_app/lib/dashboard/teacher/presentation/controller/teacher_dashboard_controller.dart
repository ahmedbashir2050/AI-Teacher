import 'package:get/get.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/config/api_endpoints.dart';
import '../../../../core/utils/logger.dart';

class TeacherDashboardController extends GetxController {
  final DioClient dioClient;

  TeacherDashboardController({required this.dioClient});

  final _isLoading = false.obs;
  bool get isLoading => _isLoading.value;

  final _answers = <dynamic>[].obs;
  List<dynamic> get answers => _answers;

  @override
  void onInit() {
    super.onInit();
    fetchAnswers();
  }

  Future<void> fetchAnswers() async {
    _isLoading.value = true;
    try {
      final response = await dioClient.get(ApiEndpoints.teacherAnswers);
      _answers.assignAll(response.data);
    } catch (e) {
      AppLogger.e('Failed to fetch answers: $e');
    } finally {
      _isLoading.value = false;
    }
  }

  Future<void> verifyAnswer(String answerId, bool verified, String comment) async {
    try {
      await dioClient.post('${ApiEndpoints.verifyAnswer}/$answerId/verify', data: {
        'verified': verified,
        'comment': comment,
      });
      fetchAnswers(); // Refresh
      Get.snackbar('Success', 'Answer verified successfully');
    } catch (e) {
      AppLogger.e('Failed to verify answer: $e');
      Get.snackbar('Error', 'Failed to verify answer');
    }
  }
}
