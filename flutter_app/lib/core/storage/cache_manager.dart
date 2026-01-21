import 'package:hive_flutter/hive_flutter.dart';

class CacheManager {
  static const String _cacheBoxName = 'app_cache';

  Future<void> cacheData<T>(String key, T data) async {
    final box = await Hive.openBox(_cacheBoxName);
    await box.put(key, data);
  }

  Future<T?> getCachedData<T>(String key) async {
    final box = await Hive.openBox(_cacheBoxName);
    return box.get(key) as T?;
  }

  Future<void> clearCache() async {
    final box = await Hive.openBox(_cacheBoxName);
    await box.clear();
  }
}
