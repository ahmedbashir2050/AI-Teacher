import 'package:get/get.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../network/network_info.dart';
import '../security/token_manager.dart';
import '../network/dio_client.dart';
import '../storage/cache_manager.dart';

class DependencyInjector {
  static Future<void> init() async {
    // External
    Get.lazyPut(() => Connectivity());
    Get.lazyPut(() => const FlutterSecureStorage());

    // Core
    Get.lazyPut<NetworkInfo>(() => NetworkInfoImpl(Get.find()));
    Get.lazyPut(() => TokenManager(Get.find()));
    Get.lazyPut(() => DioClient(Get.find()));
    Get.lazyPut(() => CacheManager());

    // Auth will be initialized in its own binding or here
  }
}
