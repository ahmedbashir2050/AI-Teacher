import 'app_config.dart';

class Env {
  static late AppConfig config;

  static void init({required Environment env}) {
    switch (env) {
      case Environment.development:
        config = AppConfig(
          apiBaseUrl: 'http://localhost:80/api/v1',
          environment: Environment.development,
          appName: 'AI Teacher (Dev)',
        );
        break;
      case Environment.staging:
        config = AppConfig(
          apiBaseUrl: 'https://staging.ai-teacher.com/api/v1',
          environment: Environment.staging,
          appName: 'AI Teacher (Staging)',
        );
        break;
      case Environment.production:
        config = AppConfig(
          apiBaseUrl: 'https://api.ai-teacher.com/api/v1',
          environment: Environment.production,
          appName: 'AI Teacher',
        );
        break;
    }
  }
}
