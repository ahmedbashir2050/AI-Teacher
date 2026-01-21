import 'package:equatable/equatable.dart';

class User extends Equatable {
  final String id;
  final String email;
  final String role;
  final String? fullName;
  final String? facultyId;

  const User({
    required this.id,
    required this.email,
    required this.role,
    this.fullName,
    this.facultyId,
  });

  @override
  List<Object?> get props => [id, email, role, fullName, facultyId];
}
