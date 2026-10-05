import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:frontend/feature/dashboard/screens/dashboard_screen.dart';
import 'package:frontend/feature/auth/providers/auth_provider.dart';
import 'package:frontend/feature/auth/screens/login_screen.dart';
import 'package:frontend/feature/auth/screens/register_screen.dart';
import 'package:frontend/feature/allocations/screens/allocation_setup_screen.dart';
import 'package:frontend/shared/widgets/splash_screen.dart';

import '../../shared/widgets/startup_gate.dart';

class AppRouter {
  AppRouter._();

  static GoRouter createRouter(WidgetRef ref) {
    return GoRouter(
      initialLocation: '/splash',

      redirect: (context, state) {
        final authState = ref.read(authProvider);

        final location = state.matchedLocation;
        final isAuthRoute = location == '/login' || location == '/register';

        if (authState.status == AuthStatus.loading) {
          if (location == '/splash' || isAuthRoute) {
            return null;
          }

          return '/splash';
        }

        final isAuthenticated = authState.status == AuthStatus.authenticated;

        if (!isAuthenticated) {
          if (isAuthRoute) {
            return null;
          }

          return '/login';
        }

        if (isAuthenticated && (isAuthRoute || location == '/splash')) {
          return '/startup';
        }

        return null;
      },

      routes: [
        GoRoute(
          path: '/splash',
          builder: (context, state) {
            return const SplashScreen();
          },
        ),

        GoRoute(
          path: '/startup',
          builder: (context, state) {
            return const StartupGate();
          },
        ),

        GoRoute(
          path: '/login',
          builder: (context, state) {
            return const LoginScreen();
          },
        ),

        GoRoute(
          path: '/register',
          builder: (context, state) {
            return const RegisterScreen();
          },
        ),

        GoRoute(
          path: '/setup',
          builder: (context, state) {
            return const AllocationSetupScreen();
          },
        ),

        GoRoute(
          path: '/',
          builder: (context, state) {
            return const DashboardScreen();
          },
        ),
      ],
    );
  }
}
