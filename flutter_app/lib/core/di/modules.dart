import 'package:get/get.dart';
import '../../auth/presentation/controller/auth_controller.dart';
import '../../auth/data/repositories/auth_repository_impl.dart';
import '../../auth/domain/usecases/login_email.dart';
import '../../auth/data/datasources/auth_remote_ds.dart';
import '../../auth/data/datasources/auth_local_ds.dart';

class AuthBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<AuthRemoteDataSource>(() => AuthRemoteDataSourceImpl(Get.find()));
    Get.lazyPut<AuthLocalDataSource>(() => AuthLocalDataSourceImpl(Get.find()));
    Get.lazyPut<AuthRepositoryImpl>(() => AuthRepositoryImpl(
      remoteDataSource: Get.find(),
      localDataSource: Get.find(),
      networkInfo: Get.find(),
    ));
    Get.lazyPut(() => LoginEmail(Get.find<AuthRepositoryImpl>()));
    Get.put(AuthController(loginEmail: Get.find()), permanent: true);
  }
}
