import 'package:get/get.dart';
import '../../auth/presentation/controller/auth_controller.dart';

class RBACGuard extends GetMiddleware {
  final List<String> allowedRoles;

  RBACGuard({required this.allowedRoles});

  @override
  RouteSettings? redirect(String? route) {
    final authController = Get.find<AuthController>();

    if (!authController.isLoggedIn) {
      return const RouteSettings(name: '/login');
    }

    final userRole = authController.user?.role;
    if (userRole == null || !allowedRoles.contains(userRole)) {
      return const RouteSettings(name: '/unauthorized');
    }

    return null;
  }
}
