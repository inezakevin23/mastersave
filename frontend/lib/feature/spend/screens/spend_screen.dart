import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../dashboard/models/dashboard_models.dart';
import '../../dashboard/providers/dashboard_provider.dart';

class SpendScreen extends ConsumerWidget {
  const SpendScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Spend')),
      body: dashboard.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(error.toString(), textAlign: TextAlign.center),
          ),
        ),
        data: (data) {
          final spend = data.spend;
          final current = spend.currentRelease;
          final due = spend.withdrawalRelease;

          return RefreshIndicator(
            onRefresh: () =>
                ref.read(dashboardProvider.notifier).refreshDashboard(),
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(20),
              children: [
                Text(
                  'Weekly allowance',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '${data.currency} ${formatMoney(spend.weeklyAmount ?? 0)}',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 20),
                if (current != null)
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(
                      'Week ${spend.currentWeek ?? ''} of ${spend.totalWeeks ?? ''}',
                    ),
                    subtitle: Text(
                      'Transfer status: ${current.status ?? 'UNKNOWN'}',
                    ),
                    trailing: Text(
                      '${data.currency} ${formatMoney(current.amount)}',
                    ),
                  )
                else if (due == null && spend.nextRelease == null)
                  const Text('No allowance release is currently scheduled.'),
                if (due != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    'Week ${due.weekNumber} is ready to withdraw.',
                    style: const TextStyle(color: Color(0xFF536070)),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    height: 52,
                    child: ElevatedButton.icon(
                      onPressed: () => context.push(
                        '/withdraw-allowance/${due.id}',
                      ),
                      icon: const Icon(Icons.account_balance_wallet_outlined),
                      label: Text(
                        'Withdraw ${data.currency} ${formatMoney(due.amount)}',
                      ),
                    ),
                  ),
                ] else if (current?.status == 'PROCESSING') ...[
                  const SizedBox(height: 12),
                  const Text(
                    'Your transfer is processing. Its status will update after the provider confirms it.',
                    style: TextStyle(color: Color(0xFF536070)),
                  ),
                ] else if (spend.nextRelease != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    'Next release: ${spend.nextRelease!.scheduledAt?.toLocal() ?? 'Scheduled'}',
                    style: const TextStyle(color: Color(0xFF536070)),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}
