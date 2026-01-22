import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app/core/auth/token_manager.dart';

void main() {
  group('RBACGuard Permissions', () {
    test('Teacher should have permission to verify, curriculum, and feedback', () {
      expect(RBACGuard.hasPermission(UserRole.teacher, 'verify'), true);
      expect(RBACGuard.hasPermission(UserRole.teacher, 'curriculum'), true);
      expect(RBACGuard.hasPermission(UserRole.teacher, 'feedback'), true);
      expect(RBACGuard.hasPermission(UserRole.teacher, 'super'), false);
    });
  });
}
