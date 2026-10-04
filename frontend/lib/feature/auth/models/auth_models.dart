class ScholarProfile {
  final String id;
  final String? scholarId;
  final String institution;
  final String country;
  final String? program;
  final String? studyLevel;
  final int? graduationYear;
  final String verificationStatus;

  const ScholarProfile({
    required this.id,
    required this.scholarId,
    required this.institution,
    required this.country,
    required this.program,
    required this.studyLevel,
    required this.graduationYear,
    required this.verificationStatus,
  });

  factory ScholarProfile.fromJson(Map<String, dynamic> json) {
    return ScholarProfile(
      id: json['id'].toString(),
      scholarId: json['scholar_id'] as String?,
      institution: json['institution'] as String,
      country: json['country'] as String,
      program: json['program'] as String?,
      studyLevel: json['study_level'] as String?,
      graduationYear: json['graduation_year'] as int?,
      verificationStatus: json['verification_status'] as String,
    );
  }
}

class UserModel {
  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final String phone;
  final String role;
  final ScholarProfile? scholarProfile;

  const UserModel({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.phone,
    required this.role,
    required this.scholarProfile,
  });

  String get fullName => '$firstName $lastName';

  factory UserModel.fromJson(Map<String, dynamic> json) {
    final profile = json['scholar_profile'];

    return UserModel(
      id: json['id'].toString(),
      email: json['email'] as String,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      phone: json['phone'] as String,
      role: json['role'] as String,
      scholarProfile: profile != null
          ? ScholarProfile.fromJson(Map<String, dynamic>.from(profile))
          : null,
    );
  }
}

class AuthResponse {
  final String accessToken;
  final String refreshToken;
  final UserModel user;

  const AuthResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      accessToken: json['access'] as String,
      refreshToken: json['refresh'] as String,
      user: UserModel.fromJson(Map<String, dynamic>.from(json['user'])),
    );
  }
}
