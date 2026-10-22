class UserProfile {
  final int hrId;
  final String fullName;
  final String login;
  final String role;

  UserProfile({
    required this.hrId,
    required this.fullName,
    required this.login,
    this.role = 'hr',
  });

  bool get isAdmin => role == 'admin';

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      hrId: json['hr_id'] ?? 0,
      fullName: json['full_name'] ?? '',
      login: json['login'] ?? '',
      role: json['role'] ?? 'hr',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'hr_id': hrId,
      'full_name': fullName,
      'login': login,
      'role': role,
    };
  }
}

class LoginResponse {
  final String accessToken;
  final String tokenType;
  final UserProfile user;

  LoginResponse({
    required this.accessToken,
    required this.tokenType,
    required this.user,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      accessToken: json['access_token'] ?? '',
      tokenType: json['token_type'] ?? 'bearer',
      user: UserProfile.fromJson(json['user'] ?? {}),
    );
  }
}
