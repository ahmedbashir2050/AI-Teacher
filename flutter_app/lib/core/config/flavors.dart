enum Flavor { dev, staging, prod }

class FlavorConfig {
  static late Flavor flavor;

  static bool get isDev => flavor == Flavor.dev;
  static bool get isStaging => flavor == Flavor.staging;
  static bool get isProd => flavor == Flavor.prod;
}
