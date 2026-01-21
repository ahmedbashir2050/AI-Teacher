import 'dart:convert';
import 'package:crypto/crypto.dart';

class EncryptionUtils {
  static String hashPassword(String password) {
    var bytes = utf8.encode(password);
    return sha256.convert(bytes).toString();
  }
}
