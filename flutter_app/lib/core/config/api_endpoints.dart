class ApiEndpoints {
  static const String login = '/auth/login';
  static const String googleLogin = '/auth/google';
  static const String refreshToken = '/auth/refresh';
  static const String logout = '/auth/logout';
  static const String userProfile = '/users/me';

  // Teacher endpoints
  static const String teacherAnswers = '/teacher/chat/answers';
  static const String verifyAnswer = '/answers'; // /answers/{id}/verify
  static const String studentAiConfidence = '/students'; // /students/{id}/ai-confidence
  static const String courseProgress = '/courses'; // /courses/{id}/progress

  // Admin endpoints
  static const String curriculumApprove = '/curriculum'; // /curriculum/{id}/approve
}
