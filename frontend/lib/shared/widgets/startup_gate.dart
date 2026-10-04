import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:frontend/feature/allocations/providers/allocation_provider.dart';
import 'package:frontend/feature/auth/providers/auth_provider.dart';

class StartupGate extends ConsumerStatefulWidget {
  const StartupGate({super.key});

  @override
  ConsumerState<StartupGate> createState() => _StartupGateState();
}

class _StartupGateState extends ConsumerState<StartupGate> {
  bool _navigated = false;

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    if (authState.status != AuthStatus.authenticated) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final status = ref.watch(allocationSetupStatusProvider);

    status.whenData((data) {
      if (_navigated) {
        return;
      }

      _navigated = true;

      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) {
          return;
        }

        if (data.setupComplete) {
          context.go('/');
        } else {
          context.go('/setup');
        }
      });
    });

    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}
