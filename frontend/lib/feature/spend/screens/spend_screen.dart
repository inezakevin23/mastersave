import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

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
                  spend.plans.length > 1
                      ? 'Combined weekly allowance'
                      : 'Weekly allowance',
                  style: Theme.of(context).textTheme.headlineSmall
                      ?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                Text(
                  '${data.currency} ${formatMoney(spend.weeklyAmount ?? 0)}',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 20),
                if (spend.plans.isNotEmpty) ...[
                  const Text(
                    'Active allowance plans',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 10),
                  ...spend.plans.asMap().entries.map((entry) {
                    final plan = entry.value;
                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: CircleAvatar(child: Text('${entry.key + 1}')),
                        title: Text(
                          'Plan ${entry.key + 1}: ${data.currency} '
                          '${formatMoney(plan.allocated)}',
                        ),
                        subtitle: Text(
                          '${data.currency} ${formatMoney(plan.weeklyAmount)} '
                          'per week for ${plan.numberOfWeeks} weeks',
                        ),
                        trailing: plan.currentWeek == null
                            ? null
                            : Text('Week ${plan.currentWeek}'),
                      ),
                    );
                  }),
                  const SizedBox(height: 12),
                ],
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
                if (spend.withdrawalReleases.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  const Text(
                    'Ready to withdraw',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 8),
                  ...spend.withdrawalReleases.map(
                    (release) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: SizedBox(
                        height: 52,
                        child: ElevatedButton.icon(
                          onPressed: () =>
                              context.push('/withdraw-allowance/${release.id}'),
                          icon: const Icon(
                            Icons.account_balance_wallet_outlined,
                          ),
                          label: Text(
                            'Week ${release.weekNumber}: withdraw '
                            '${data.currency} ${formatMoney(release.amount)}',
                          ),
                        ),
                      ),
                    ),
                  ),
                ] else if (due != null) ...[
                  const SizedBox(height: 12),
                  SizedBox(
                    height: 52,
                    child: ElevatedButton.icon(
                      onPressed: () =>
                          context.push('/withdraw-allowance/${due.id}'),
                      icon: const Icon(Icons.account_balance_wallet_outlined),
                      label: Text(
                        'Withdraw ${data.currency} ${formatMoney(due.amount)}',
                      ),
                    ),
                  ),
                ] else if (spend.nextRelease != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    'Next allowance week begins ${spend.nextRelease!.scheduledAt == null ? 'soon' : DateFormat('EEE, MMM d').format(spend.nextRelease!.scheduledAt!.toLocal())}',
                    style: const TextStyle(color: Color(0xFF536070)),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'You can request this allowance once its week begins. Withdrawals are manual.',
                    style: TextStyle(color: Color(0xFF536070)),
                  ),
                ] else if (current?.status == 'PROCESSING') ...[
                  const SizedBox(height: 12),
                  const Text(
                    'This allowance payout is already processing. Its status updates after the provider confirms it.',
                    style: TextStyle(color: Color(0xFF536070)),
                  ),
                ] else if (current?.status == 'RELEASED') ...[
                  const SizedBox(height: 12),
                  const Text(
                    'This allowance has already been paid.',
                    style: TextStyle(color: Color(0xFF536070)),
                  ),
                ] else if (current?.status == 'FAILED') ...[
                  const SizedBox(height: 12),
                  const Text(
                    'The last payout failed. Contact support before trying again.',
                    style: TextStyle(color: Color(0xFF536070)),
                  ),
                ] else if (current == null) ...[
                  const SizedBox(height: 12),
                  const Text(
                    'No allowance is due for withdrawal yet.',
                    style: TextStyle(color: Color(0xFF536070)),
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
