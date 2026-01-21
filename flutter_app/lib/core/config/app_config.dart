enum Environment { development, staging, production }

class AppConfig {
  final String apiBaseUrl;
  final Environment environment;
  final String appName;

  AppConfig({
    required this.apiBaseUrl,
    required this.environment,
    required this.appName,
  });
}
