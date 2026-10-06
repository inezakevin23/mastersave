import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../dashboard/models/dashboard_models.dart';
import '../../dashboard/providers/dashboard_provider.dart';

class SavingsScreen extends ConsumerWidget {
  const SavingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Save')),

      body: dashboard.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(error.toString(), textAlign: TextAlign.center),
          ),
        ),
        data: (data) => RefreshIndicator(
          onRefresh: () =>
              ref.read(dashboardProvider.notifier).refreshDashboard(),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
            children: [
              Text(
                'Savings balance',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 6),
              Text(
                '${data.currency} ${formatMoney(data.save.totalSaved)}',
                style: Theme.of(context).textTheme.headlineSmall
                    ?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 20),
              if (data.save.buckets.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 28),
                  child: Text(
                    'Your savings goals and emergency savings will appear here.',
                    textAlign: TextAlign.center,
                  ),
                )
              else
                ...data.save.buckets.map(
                  (bucket) => _SavingsBucketRow(
                    bucket: bucket,
                    currency: data.currency,
                  ),
                ),
              const SizedBox(height: 20),
              OutlinedButton.icon(
                onPressed: () => context.push('/withdraw'),
                icon: const Icon(Icons.account_balance_wallet_outlined),
                label: const Text('Withdraw savings'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SavingsBucketRow extends StatelessWidget {
  const _SavingsBucketRow({required this.bucket, required this.currency});

  final SavingsBucketSummary bucket;
  final String currency;

  @override
  Widget build(BuildContext context) {
    final isGoal = bucket.type == 'GOAL_LOCK';
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(
        isGoal ? Icons.lock_outline : Icons.savings_outlined,
        color: isGoal ? const Color(0xFFDC2626) : const Color(0xFF059669),
      ),
      title: Text(bucket.name),
      subtitle: Text(
        bucket.isLocked ? 'Goal Lock · Locked' : 'Available to withdraw',
      ),
      trailing: Text(
        '$currency ${formatMoney(bucket.balance)}',
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
    );
  }
}
