import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'routing/app_router.dart';
import 'theme/app_theme.dart';
import 'core/di/modules.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'AI Teacher',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      initialRoute: AppRouter.initial,
      getPages: AppRouter.routes,
      initialBinding: AuthBinding(),
    );
  }
}
