import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('End-to-End Flow Test', () {
    testWidgets('Login -> Student Chat -> Dashboard Navigation', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      // 1. Verify Login Page
      expect(find.text('AI Teacher'), findsOneWidget);

      // 2. Perform Login
      await tester.enterText(find.byType(TextField).first, 'student@test.com');
      await tester.enterText(find.byType(TextField).last, 'password');
      await tester.tap(find.byType(ElevatedButton));
      await tester.pumpAndSettle();

      // 3. Verify Student Dashboard
      expect(find.text('Student Dashboard'), findsOneWidget);

      // 4. Navigate to Chat
      await tester.tap(find.text('Ask AI'));
      await tester.pumpAndSettle();

      // 5. Verify Chat UI
      expect(find.text('AI Tutor'), findsOneWidget);
      await tester.enterText(find.byType(TextField), 'Hello AI');
      await tester.tap(find.byIcon(Icons.send));
      await tester.pumpAndSettle();

      expect(find.text('USER'), findsOneWidget);
      expect(find.text('Hello AI'), findsOneWidget);
    });
  });
}
