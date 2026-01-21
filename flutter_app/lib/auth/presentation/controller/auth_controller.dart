import 'package:get/get.dart';
import '../domain/entities/user.dart';
import '../domain/usecases/login_email.dart';
import '../../../core/utils/logger.dart';

class AuthController extends GetxController {
  final LoginEmail loginEmail;

  AuthController({required this.loginEmail});

  final _user = Rxn<User>();
  User? get user => _user.value;

  final _isLoading = false.obs;
  bool get isLoading => _isLoading.value;

  bool get isLoggedIn => _user.value != null;

  Future<void> login(String email, String password) async {
    _isLoading.value = true;
    final result = await loginEmail(email, password);
    result.fold(
      (failure) {
        AppLogger.e('Login failed: ${failure.message}');
        Get.snackbar('Error', failure.message);
      },
      (user) {
        _user.value = user;
        _redirectBasedOnRole(user.role);
      },
    );
    _isLoading.value = false;
  }

  void _redirectBasedOnRole(String role) {
    if (role == 'TEACHER') {
      Get.offAllNamed('/teacher-dashboard');
    } else if (role == 'ADMIN') {
      Get.offAllNamed('/admin-dashboard');
    } else {
      Get.offAllNamed('/student-dashboard');
    }
  }

  void logout() {
    _user.value = null;
    Get.offAllNamed('/login');
  }
}
