import '../../../core/network/dio_client.dart';
import '../../../core/config/api_endpoints.dart';
import '../models/user_model.dart';
import '../../../core/error/exceptions.dart';

abstract class AuthRemoteDataSource {
  Future<Map<String, dynamic>> loginEmail(String email, String password);
  Future<Map<String, dynamic>> loginGoogle(String idToken);
  Future<void> logout();
}

class AuthRemoteDataSourceImpl implements AuthRemoteDataSource {
  final DioClient client;

  AuthRemoteDataSourceImpl(this.client);

  @override
  Future<Map<String, dynamic>> loginEmail(String email, String password) async {
    try {
      final response = await client.post(ApiEndpoints.login, data: {
        'email': email,
        'password': password,
      });
      return response.data;
    } catch (e) {
      throw ServerException('Login failed');
    }
  }

  @override
  Future<Map<String, dynamic>> loginGoogle(String idToken) async {
    try {
      final response = await client.post(ApiEndpoints.googleLogin, data: {
        'id_token': idToken,
      });
      return response.data;
    } catch (e) {
      throw ServerException('Google login failed');
    }
  }

  @override
  Future<void> logout() async {
    await client.post(ApiEndpoints.logout);
  }
}
