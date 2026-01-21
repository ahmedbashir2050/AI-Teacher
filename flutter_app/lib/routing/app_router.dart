import 'package:get/get.dart';
import '../auth/presentation/screens/login_screen.dart';
import '../auth/presentation/screens/splash_screen.dart';
import '../dashboard/teacher/presentation/screens/teacher_dashboard_screen.dart';
import '../dashboard/admin/presentation/screens/admin_dashboard_screen.dart';
import '../core/security/rbac_guard.dart';
import '../core/constants/roles.dart';

class AppRouter {
  static const String initial = '/';

  static final routes = [
    GetPage(
      name: '/',
      page: () => const SplashScreen(),
    ),
    GetPage(
      name: '/login',
      page: () => LoginScreen(),
    ),
    GetPage(
      name: '/teacher-dashboard',
      page: () => const TeacherDashboardScreen(),
      middlewares: [RBACGuard(allowedRoles: [UserRoles.teacher, UserRoles.admin])],
    ),
    GetPage(
      name: '/admin-dashboard',
      page: () => const AdminDashboardScreen(),
      middlewares: [RBACGuard(allowedRoles: [UserRoles.admin, UserRoles.superAdmin])],
    ),
  ];
}
