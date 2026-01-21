import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'app.dart';
import 'core/di/injector.dart';
import 'core/config/env.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Environment
  Env.init(env: Environment.development);

  // Initialize Storage
  await Hive.initFlutter();

  // Initialize Dependency Injection
  await DependencyInjector.init();

  runApp(const App());
}
