import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/allocation_provider.dart';

class WaitingForAllowanceScreen extends ConsumerStatefulWidget {
  const WaitingForAllowanceScreen({super.key});

  @override
  ConsumerState<WaitingForAllowanceScreen> createState() =>
      _WaitingForAllowanceScreenState();
}

class _WaitingForAllowanceScreenState
    extends ConsumerState<WaitingForAllowanceScreen> {
  bool _navigated = false;
  Timer? _statusTimer;

  @override
  void initState() {
    super.initState();
    _statusTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (mounted) ref.invalidate(allocationSetupStatusProvider);
    });
  }

  @override
  void dispose() {
    _statusTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final status = ref.watch(allocationSetupStatusProvider);

    status.whenData((data) {
      final destination = data.setupComplete
          ? '/'
          : data.hasUnallocatedDeposit
          ? '/setup'
          : null;

      if (_navigated || destination == null) {
        return;
      }

      _navigated = true;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          context.go(destination);
        }
      });
    });

    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),

      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: status.when(
              loading: () => const CircularProgressIndicator(),

              error: (error, stackTrace) => _ErrorState(
                message: error.toString(),
                onRetry: () {
                  ref.invalidate(allocationSetupStatusProvider);
                },
              ),

              data: (_) => _WaitingContent(
                onRefresh: () {
                  ref.invalidate(allocationSetupStatusProvider);
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _WaitingContent extends StatelessWidget {
  final VoidCallback onRefresh;

  const _WaitingContent({required this.onRefresh});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 78,
          height: 78,
          decoration: const BoxDecoration(
            color: Color(0xFFFFF4D8),
            shape: BoxShape.circle,
          ),
          child: const Icon(
            Icons.account_balance_wallet_outlined,
            size: 36,
            color: Color(0xFFF59E0B),
          ),
        ),

        const SizedBox(height: 24),

        const Text(
          'Waiting for your allowance',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 25, fontWeight: FontWeight.w800),
        ),

        const SizedBox(height: 10),

        const Text(
          'Your MasterSave account is ready. '
          'Once your allowance is received, '
          'you will be able to divide it across '
          'Spend, Save, and Grow.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 14, height: 1.5, color: Color(0xFF536070)),
        ),

        const SizedBox(height: 28),

        SizedBox(
          width: double.infinity,
          height: 52,
          child: OutlinedButton(
            onPressed: onRefresh,
            child: const Text('Check again'),
          ),
        ),
      ],
    );
  }
}

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorState({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Text(
          'Unable to check your allowance',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
        ),

        const SizedBox(height: 10),

        Text(message, textAlign: TextAlign.center),

        const SizedBox(height: 20),

        ElevatedButton(onPressed: onRetry, child: const Text('Try again')),
      ],
    );
  }
}
