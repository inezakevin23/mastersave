import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:frontend/feature/allocations/providers/allocation_provider.dart';

class StartupGate extends ConsumerStatefulWidget {
  const StartupGate({super.key});

  @override
  ConsumerState<StartupGate> createState() => _StartupGateState();
}

class _StartupGateState extends ConsumerState<StartupGate> {
  bool _navigated = false;

  @override
  Widget build(BuildContext context) {
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
          return;
        }

        if (data.hasUnallocatedDeposit) {
          context.go('/setup');
          return;
        }

        // Scholar is authenticated but
        // hasn't received an allowance yet.
        context.go('/waiting');
      });
    });

    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}
