import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/secure_storage.dart';
import '../models/auth_models.dart';

class AuthServiceException implements Exception {
  const AuthServiceException({required this.message, this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class AuthService {
  AuthService._();

  static Future<AuthResponse> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await ApiClient.dio.post(
        '/auth/login/',
        data: {'email': email.trim().toLowerCase(), 'password': password},
      );

      final authResponse = AuthResponse.fromJson(
        Map<String, dynamic>.from(response.data),
      );

      await SecureStorage.saveTokens(
        accessToken: authResponse.accessToken,
        refreshToken: authResponse.refreshToken,
      );

      return authResponse;
    } on DioException catch (error) {
      throw _convertError(error);
    }
  }

  static Future<void> register({
    required String email,
    required String password,
    required String passwordConfirmation,
    required String firstName,
    required String lastName,
    required String phone,
    required String scholarId,
    required String institution,
    required String country,
    required String program,
    required String studyLevel,
    required int graduationYear,
  }) async {
    try {
      await ApiClient.dio.post(
        '/auth/register/',
        data: {
          'email': email.trim().toLowerCase(),
          'password': password,
          'password_confirmation': passwordConfirmation,
          'first_name': firstName.trim(),
          'last_name': lastName.trim(),
          'phone': phone.trim(),
          'profile': {
            'scholar_id': scholarId.trim(),
            'institution': institution.trim(),
            'country': country.trim().toUpperCase(),
            'program': program.trim(),
            'study_level': studyLevel.trim(),
            'graduation_year': graduationYear,
          },
        },
      );
    } on DioException catch (error) {
      throw _convertError(error);
    }
  }

  static Future<UserModel> getCurrentUser() async {
    try {
      final response = await ApiClient.dio.get('/auth/me/');

      return UserModel.fromJson(Map<String, dynamic>.from(response.data));
    } on DioException catch (error) {
      throw AuthServiceException(
        message: _convertError(error),
        statusCode: error.response?.statusCode,
      );
    }
  }

  static Future<void> logout() async {
    await SecureStorage.clearTokens();
  }

  static String _convertError(DioException error) {
    final responseMessage = _extractErrorMessage(error.response?.data);
    if (responseMessage != null && responseMessage.isNotEmpty) {
      return responseMessage;
    }

    if (error.type == DioExceptionType.connectionTimeout) {
      return 'Connection timed out.';
    }

    if (error.type == DioExceptionType.connectionError) {
      return 'Unable to connect to MasterSave.';
    }

    return 'Something went wrong. Please try again.';
  }

  static String? _extractErrorMessage(dynamic value) {
    if (value is String) {
      return value;
    }

    if (value is List) {
      for (final item in value) {
        final message = _extractErrorMessage(item);
        if (message != null && message.isNotEmpty) {
          return message;
        }
      }
      return null;
    }

    if (value is Map) {
      for (final key in [
        'detail',
        'error',
        'email',
        'password',
        'password_confirmation',
        'profile',
      ]) {
        if (value.containsKey(key)) {
          final message = _extractErrorMessage(value[key]);
          if (message != null && message.isNotEmpty) {
            return message;
          }
        }
      }

      for (final entry in value.entries) {
        if (entry.key == 'success') {
          continue;
        }
        final message = _extractErrorMessage(entry.value);
        if (message != null && message.isNotEmpty) {
          return '${entry.key}: $message';
        }
      }
    }

    return null;
  }
}
