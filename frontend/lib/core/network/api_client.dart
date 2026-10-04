import 'package:dio/dio.dart';

import '../config/app_config.dart';
import '../storage/secure_storage.dart';

class ApiClient {
  ApiClient._();

  static final Dio dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      sendTimeout: const Duration(seconds: 15),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );

  // This Dio instance is intentionally separate.
  // It does not have the authentication-refresh
  // interceptor, preventing refresh loops.
  static final Dio _refreshDio = Dio(
    BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      sendTimeout: const Duration(seconds: 15),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );

  static bool _initialized = false;

  static Future<void> Function()? onSessionExpired;

  static void initialize() {
    if (_initialized) {
      return;
    }

    _initialized = true;

    dio.interceptors.add(
      QueuedInterceptorsWrapper(
        onRequest: (options, handler) async {
          if (_isPublicAuthRequest(options)) {
            handler.next(options);
            return;
          }

          final accessToken = await SecureStorage.getAccessToken();

          if (accessToken != null && accessToken.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $accessToken';
          }

          handler.next(options);
        },

        onError: (error, handler) async {
          final request = error.requestOptions;

          final statusCode = error.response?.statusCode;

          final alreadyRetried = request.extra['authRetry'] == true;

          final isPublicRequest = _isPublicAuthRequest(request);

          // Only attempt refresh for an expired
          // authenticated request.
          if (statusCode != 401 || alreadyRetried || isPublicRequest) {
            handler.next(error);
            return;
          }

          final newAccessToken = await _refreshAccessToken();

          if (newAccessToken == null) {
            await SecureStorage.clearTokens();

            final callback = onSessionExpired;

            if (callback != null) {
              await callback();
            }

            handler.next(error);
            return;
          }

          request.headers['Authorization'] = 'Bearer $newAccessToken';

          request.extra['authRetry'] = true;

          try {
            final response = await dio.fetch(request);

            handler.resolve(response);
          } on DioException catch (retryError) {
            handler.next(retryError);
          }
        },
      ),
    );
  }

  static bool _isPublicAuthRequest(RequestOptions options) {
    final path = options.path;

    return path.endsWith('/auth/login/') ||
        path.endsWith('/auth/register/') ||
        path.endsWith('/auth/refresh/');
  }

  static Future<String?> _refreshAccessToken() async {
    try {
      final refreshToken = await SecureStorage.getRefreshToken();

      if (refreshToken == null || refreshToken.isEmpty) {
        return null;
      }

      final response = await _refreshDio.post(
        '/auth/refresh/',
        data: {'refresh': refreshToken},
      );

      final data = Map<String, dynamic>.from(response.data as Map);

      final newAccessToken = data['access'] as String?;

      if (newAccessToken == null || newAccessToken.isEmpty) {
        return null;
      }

      // Rotation is enabled on Django, so use
      // the new refresh token when supplied.
      final newRefreshToken = data['refresh'] as String? ?? refreshToken;

      await SecureStorage.saveTokens(
        accessToken: newAccessToken,
        refreshToken: newRefreshToken,
      );

      return newAccessToken;
    } on DioException {
      return null;
    }
  }
}
