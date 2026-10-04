import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/storage/secure_storage.dart';
import '../models/auth_models.dart';
import '../services/auth_service.dart';

enum AuthStatus { loading, authenticated, unauthenticated }

class AuthState {
  final AuthStatus status;
  final UserModel? user;
  final String? error;

  const AuthState({required this.status, this.user, this.error});

  factory AuthState.loading() {
    return const AuthState(status: AuthStatus.loading);
  }

  factory AuthState.unauthenticated() {
    return const AuthState(status: AuthStatus.unauthenticated);
  }

  factory AuthState.authenticated(UserModel user) {
    return AuthState(status: AuthStatus.authenticated, user: user);
  }

  factory AuthState.error(String message) {
    return AuthState(status: AuthStatus.unauthenticated, error: message);
  }
}

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    Future.microtask(initialize);
    return AuthState.loading();
  }

  Future<void> initialize() async {
    try {
      final accessToken = await SecureStorage.getAccessToken();

      if (accessToken == null || accessToken.isEmpty) {
        state = AuthState.unauthenticated();
        return;
      }

      final user = await AuthService.getCurrentUser();

      state = AuthState.authenticated(user);
    } catch (_) {
      await SecureStorage.clearTokens();

      state = AuthState.unauthenticated();
    }
  }

  Future<void> login({required String email, required String password}) async {
    state = AuthState.loading();

    try {
      final response = await AuthService.login(
        email: email,
        password: password,
      );

      state = AuthState.authenticated(response.user);
    } catch (error) {
      state = AuthState.error(error.toString());
    }
  }

  Future<void> logout() async {
    await AuthService.logout();

    state = AuthState.unauthenticated();
  }
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(
  AuthNotifier.new,
);
