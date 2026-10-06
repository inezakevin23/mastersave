import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:frontend/feature/dashboard/screens/dashboard_screen.dart';
import 'package:frontend/feature/auth/providers/auth_provider.dart';
import 'package:frontend/feature/auth/screens/login_screen.dart';
import 'package:frontend/feature/auth/screens/register_screen.dart';
import 'package:frontend/feature/allocations/screens/allocation_overview_screen.dart';
import 'package:frontend/feature/allocations/screens/allocation_setup_screen.dart';
import 'package:frontend/feature/allocations/screens/waiting_for_allowance_screen.dart';
import 'package:frontend/feature/investments/screens/grow_screen.dart';
import 'package:frontend/feature/payments/screens/withdrawal_screen.dart';
import 'package:frontend/feature/payments/screens/allowance_withdrawal_screen.dart';
import 'package:frontend/feature/profile/screens/profile_screen.dart';
import 'package:frontend/feature/savings/screens/savings_screen.dart';
import 'package:frontend/feature/spend/screens/spend_screen.dart';
import 'package:frontend/shared/widgets/app_shell.dart';
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

        if (authState.status == AuthStatus.loading) {
          if (location == '/splash') {
            return null;
          }

          return '/splash';
        }

        final isAuthenticated = authState.status == AuthStatus.authenticated;
        final isAuthRoute = location == '/login' || location == '/register';

        if (!isAuthenticated) {
          if (isAuthRoute) {
            return null;
          }

          return '/login';
        }

        if (isAuthRoute || location == '/splash') {
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
          path: '/waiting',
          builder: (context, state) {
            return const WaitingForAllowanceScreen();
          },
        ),

        GoRoute(
          path: '/setup',
          builder: (context, state) {
            return const AllocationSetupScreen();
          },
        ),

        ShellRoute(
          builder: (context, state, child) {
            return AppShell(child: child);
          },
          routes: [
            GoRoute(
              path: '/',
              builder: (context, state) {
                return const DashboardScreen();
              },
            ),
            GoRoute(
              path: '/allocation',
              builder: (context, state) {
                return const AllocationOverviewScreen();
              },
            ),
            GoRoute(
              path: '/spend',
              builder: (context, state) {
                return const SpendScreen();
              },
            ),
            GoRoute(
              path: '/save',
              builder: (context, state) {
                return const SavingsScreen();
              },
            ),
            GoRoute(
              path: '/withdraw',
              builder: (context, state) {
                return const WithdrawalScreen();
              },
            ),
            GoRoute(
              path: '/withdraw-allowance/:releaseId',
              builder: (context, state) {
                return AllowanceWithdrawalScreen(
                  releaseId: state.pathParameters['releaseId']!,
                );
              },
            ),
            GoRoute(
              path: '/grow',
              builder: (context, state) {
                return const GrowScreen();
              },
            ),
            GoRoute(
              path: '/profile',
              builder: (context, state) {
                return const ProfileScreen();
              },
            ),
          ],
        ),
      ],
    );
  }
}
