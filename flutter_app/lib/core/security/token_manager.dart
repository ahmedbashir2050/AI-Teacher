import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/storage_keys.dart';

class TokenManager {
  final FlutterSecureStorage _storage;

  TokenManager(this._storage);

  Future<void> saveTokens({required String access, required String refresh}) async {
    await _storage.write(key: StorageKeys.accessToken, value: access);
    await _storage.write(key: StorageKeys.refreshToken, value: refresh);
  }

  Future<String?> getAccessToken() async => await _storage.read(key: StorageKeys.accessToken);
  Future<String?> getRefreshToken() async => await _storage.read(key: StorageKeys.refreshToken);

  Future<void> deleteTokens() async {
    await _storage.delete(key: StorageKeys.accessToken);
    await _storage.delete(key: StorageKeys.refreshToken);
  }

  Future<String?> getFacultyId() async {
    // In a real app, this might be stored in secure storage or a regular hive box
    // depending on sensitivity.
    return await _storage.read(key: 'faculty_id');
  }
}
