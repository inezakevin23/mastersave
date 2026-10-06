import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:go_router/go_router.dart';

import '../../auth/models/auth_models.dart';
import '../../auth/providers/auth_provider.dart';
import '../../allocations/providers/allocation_provider.dart';
import '../models/dashboard_models.dart';
import '../providers/dashboard_provider.dart';

enum DashboardSection { spend, save, grow }

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen>
    with WidgetsBindingObserver {
  DashboardSection section = DashboardSection.spend;
  Timer? _refreshTimer;
  bool _allocationNavigationPending = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _refreshTimer = Timer.periodic(const Duration(seconds: 20), (_) {
      if (mounted &&
          WidgetsBinding.instance.lifecycleState == AppLifecycleState.resumed) {
        ref.read(dashboardProvider.notifier).refreshDashboard();
        ref.invalidate(allocationSetupStatusProvider);
      }
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      ref.read(dashboardProvider.notifier).refreshDashboard();
      ref.invalidate(allocationSetupStatusProvider);
    }
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dashboard = ref.watch(dashboardProvider);
    final allocationStatus = ref.watch(allocationSetupStatusProvider);

    allocationStatus.whenData((status) {
      if (status.hasUnallocatedDeposit && !_allocationNavigationPending) {
        _allocationNavigationPending = true;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) context.go('/setup');
        });
      } else if (!status.hasUnallocatedDeposit) {
        _allocationNavigationPending = false;
      }
    });

    final user = ref.watch(authProvider).user;

    return Scaffold(
      backgroundColor: const Color(0xFFFDFDFD),

      body: SafeArea(
        child: dashboard.when(
          loading: () => const Center(child: CircularProgressIndicator()),

          error: (error, stackTrace) => _ErrorView(
            message: error.toString(),
            onRetry: () {
              ref.read(dashboardProvider.notifier).refreshDashboard();
            },
          ),

          data: (data) => RefreshIndicator(
            onRefresh: () {
              return ref.read(dashboardProvider.notifier).refreshDashboard();
            },

            child: ListView(
              padding: const EdgeInsets.fromLTRB(24, 24, 24, 32),

              children: [
                _Header(user: user),

                const SizedBox(height: 28),

                _TotalDeposited(data: data),

                const SizedBox(height: 18),

                _AllocationBar(data: data),

                const SizedBox(height: 12),

                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton.icon(
                    onPressed: () {
                      context.go('/allocation');
                    },
                    icon: const Icon(
                      Icons.account_balance_wallet_outlined,
                      size: 18,
                    ),
                    label: const Text('View allocation'),
                  ),
                ),

                const SizedBox(height: 18),

                _SectionSelector(
                  selected: section,
                  data: data,
                  onChanged: (value) {
                    setState(() {
                      section = value;
                    });
                  },
                ),

                const SizedBox(height: 24),

                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 220),
                  child: switch (section) {
                    DashboardSection.spend => _SpendSection(
                      key: const ValueKey('spend'),
                      data: data,
                    ),

                    DashboardSection.save => _SaveSection(
                      key: const ValueKey('save'),
                      data: data,
                    ),

                    DashboardSection.grow => _GrowSection(
                      key: const ValueKey('grow'),
                      data: data,
                    ),
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// --------------------------------------------------
// Header
// --------------------------------------------------

class _Header extends StatelessWidget {
  final UserModel? user;

  const _Header({required this.user});

  @override
  Widget build(BuildContext context) {
    final initials = _initials(user);

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                Container(
                  width: 20,
                  height: 20,
                  decoration: BoxDecoration(
                    color: const Color(0xFFDC2626),
                    borderRadius: BorderRadius.circular(5),
                  ),
                ),

                Positioned(
                  top: -4,
                  right: -4,
                  child: Container(
                    width: 9,
                    height: 9,
                    decoration: const BoxDecoration(
                      color: Color(0xFFF59E0B),
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(width: 9),

            const Text(
              'MasterSave',
              style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800),
            ),
          ],
        ),

        Container(
          width: 42,
          height: 42,
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFFDC2626), Color(0xFFF59E0B)],
            ),
            shape: BoxShape.circle,
          ),
          alignment: Alignment.center,
          child: Text(
            initials,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w800,
              fontSize: 13,
            ),
          ),
        ),
      ],
    );
  }

  String _initials(UserModel? user) {
    if (user == null) {
      return 'MS';
    }

    final first = user.firstName.isNotEmpty ? user.firstName[0] : '';

    final last = user.lastName.isNotEmpty ? user.lastName[0] : '';

    return '$first$last'.toUpperCase();
  }
}

// --------------------------------------------------
// Total deposited
// --------------------------------------------------

class _TotalDeposited extends StatelessWidget {
  final DashboardData data;

  const _TotalDeposited({required this.data});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'TOTAL DEPOSITED',
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            letterSpacing: 1.1,
            color: Color(0xFF8490A0),
          ),
        ),

        const SizedBox(height: 7),

        RichText(
          text: TextSpan(
            children: [
              TextSpan(
                text: '${data.currency} ',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF98A1AD),
                ),
              ),

              TextSpan(
                text: formatMoney(data.totalDeposited),
                style: const TextStyle(
                  fontSize: 40,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -1.2,
                  color: Colors.black,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 3),

        const Text(
          'Split across Spend, Save, and Grow',
          style: TextStyle(fontSize: 13, color: Color(0xFF536070)),
        ),
      ],
    );
  }
}

// --------------------------------------------------
// Allocation bar
// --------------------------------------------------

class _AllocationBar extends StatelessWidget {
  final DashboardData data;

  const _AllocationBar({required this.data});

  @override
  Widget build(BuildContext context) {
    final total = data.totalDeposited;

    if (total <= 0) {
      return Container(
        height: 6,
        decoration: BoxDecoration(
          color: const Color(0xFFE7E7E7),
          borderRadius: BorderRadius.circular(8),
        ),
      );
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: SizedBox(
        height: 6,

        child: Row(
          children: [
            if (data.spend.allocated > 0)
              Expanded(
                flex: data.spend.allocated,
                child: Container(color: const Color(0xFFDC2626)),
              ),

            if (data.save.allocated > 0)
              Expanded(
                flex: data.save.allocated,
                child: Container(color: const Color(0xFFF59E0B)),
              ),

            if (data.grow.allocated > 0)
              Expanded(
                flex: data.grow.allocated,
                child: Container(color: Colors.black),
              ),
          ],
        ),
      ),
    );
  }
}

// --------------------------------------------------
// Selector
// --------------------------------------------------

class _SectionSelector extends StatelessWidget {
  final DashboardSection selected;
  final DashboardData data;
  final ValueChanged<DashboardSection> onChanged;

  const _SectionSelector({
    required this.selected,
    required this.data,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _SelectorItem(
            title: 'Spend',
            amount: data.spend.allocated,
            selected: selected == DashboardSection.spend,
            onTap: () => onChanged(DashboardSection.spend),
          ),
        ),

        const SizedBox(width: 10),

        Expanded(
          child: _SelectorItem(
            title: 'Save',
            amount: data.save.allocated,
            selected: selected == DashboardSection.save,
            onTap: () => onChanged(DashboardSection.save),
          ),
        ),

        const SizedBox(width: 10),

        Expanded(
          child: _SelectorItem(
            title: 'Grow',
            amount: data.grow.allocated,
            selected: selected == DashboardSection.grow,
            onTap: () => onChanged(DashboardSection.grow),
          ),
        ),
      ],
    );
  }
}

class _SelectorItem extends StatelessWidget {
  final String title;
  final int amount;
  final bool selected;
  final VoidCallback onTap;

  const _SelectorItem({
    required this.title,
    required this.amount,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),

        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),

        decoration: BoxDecoration(
          color: selected ? const Color(0xFFDC2626) : const Color(0xFFF1F1F1),
          borderRadius: BorderRadius.circular(15),

          border: Border.all(
            color: selected ? Colors.black : Colors.transparent,
            width: selected ? 2 : 0,
          ),

          boxShadow: selected
              ? [
                  BoxShadow(
                    color: const Color(0xFFDC2626).withValues(alpha: 0.18),
                    blurRadius: 14,
                    offset: const Offset(0, 7),
                  ),
                ]
              : null,
        ),

        child: Column(
          children: [
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: selected ? Colors.white : const Color(0xFF617084),
                fontWeight: FontWeight.w700,
                fontSize: 14,
              ),
            ),

            const SizedBox(height: 2),

            Text(
              '${formatMoney(amount ~/ 1000)}K',
              style: TextStyle(
                color: selected ? Colors.white : const Color(0xFF8D96A2),
                fontWeight: FontWeight.w600,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// --------------------------------------------------
// Spend
// --------------------------------------------------

class _SpendSection extends StatelessWidget {
  final DashboardData data;

  const _SpendSection({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final spend = data.spend;
    final currentRelease = spend.currentRelease;
    final nextRelease = spend.nextRelease;
    final readyReleases = spend.withdrawalReleases;
    final manualReleaseId = readyReleases.isNotEmpty
        ? readyReleases.first.id
        : null;
    final weeklyAmount = spend.weeklyAmount ?? 0;
    final releaseStatus = currentRelease?.status;
    final statusColor = switch (releaseStatus) {
      'RELEASED' => const Color(0xFF059669),
      'PROCESSING' => const Color(0xFFF59E0B),
      'FAILED' => const Color(0xFFDC2626),
      _ => const Color(0xFF697586),
    };

    return Column(
      children: [
        _DashboardCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _CardLabel(text: 'WEEKLY SPEND ALLOCATION'),

              const SizedBox(height: 12),

              _MoneyLine(
                currency: data.currency,
                amount: weeklyAmount,
                amountSize: 35,
              ),

              const SizedBox(height: 12),

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    currentRelease == null
                        ? 'No current release'
                        : 'Week ${spend.currentWeek} of ${spend.totalWeeks}',
                    style: const TextStyle(
                      fontSize: 13,
                      color: Color(0xFF536070),
                    ),
                  ),
                  _StatusBadge(
                    label: releaseStatus ?? 'SCHEDULED',
                    color: statusColor,
                  ),
                ],
              ),
            ],
          ),
        ),

        const SizedBox(height: 14),

        _DashboardCard(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Next release',
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      _releaseText(nextRelease?.scheduledAt),
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF536070),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Flexible(
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: Alignment.centerRight,
                  child: _MoneyLine(
                    currency: data.currency,
                    amount: nextRelease?.amount ?? weeklyAmount,
                    amountSize: 20,
                  ),
                ),
              ),
            ],
          ),
        ),
        if (manualReleaseId != null) ...[
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () =>
                  context.push('/withdraw-allowance/$manualReleaseId'),
              icon: const Icon(Icons.account_balance_wallet_outlined),
              label: Text("Withdraw this week's allowance"),
            ),
          ),
          const Text(
            'Manual payout: you choose when to submit the request.',
            style: TextStyle(fontSize: 12, color: Color(0xFF536070)),
          ),
        ],
      ],
    );
  }

  String _releaseText(DateTime? date) {
    if (date == null) {
      return 'No upcoming release scheduled';
    }

    final day = DateFormat('EEEE').format(date);

    return 'Available from $day';
  }
}

// --------------------------------------------------
// Save
// --------------------------------------------------

class _SaveSection extends StatelessWidget {
  final DashboardData data;

  const _SaveSection({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _DashboardCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _CardLabel(text: 'TOTAL SAVED'),

              const SizedBox(height: 10),

              _MoneyLine(
                currency: data.currency,
                amount: data.save.totalSaved,
                amountSize: 35,
              ),

              const SizedBox(height: 8),

              const Text(
                'Saved across your MasterSave goals',
                style: TextStyle(fontSize: 13, color: Color(0xFF536070)),
              ),
            ],
          ),
        ),

        const SizedBox(height: 14),

        ...data.save.buckets.map(
          (bucket) => Padding(
            padding: const EdgeInsets.only(bottom: 14),
            child: _SavingsBucketCard(bucket: bucket, currency: data.currency),
          ),
        ),
      ],
    );
  }
}

class _SavingsBucketCard extends StatelessWidget {
  final SavingsBucketSummary bucket;
  final String currency;

  const _SavingsBucketCard({required this.bucket, required this.currency});

  @override
  Widget build(BuildContext context) {
    return _DashboardCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      bucket.name,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),

                    const SizedBox(height: 5),

                    Text(
                      bucket.type == 'GOAL_LOCK'
                          ? 'Locked until target is reached'
                          : 'Available for genuine emergencies',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF536070),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 8),
              Flexible(
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: Alignment.centerRight,
                  child: _MoneyLine(
                    currency: currency,
                    amount: bucket.balance,
                    amountSize: 18,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          _StatusBadge(
            label: bucket.isLocked
                ? 'LOCKED'
                : bucket.type == 'EMERGENCY'
                ? 'FLEXIBLE'
                : 'COMPLETED',
            color: bucket.isLocked
                ? const Color(0xFFDC2626)
                : bucket.type == 'EMERGENCY'
                ? const Color(0xFFF59E0B)
                : const Color(0xFF059669),
          ),

          if (bucket.targetAmount != null &&
              bucket.progressPercentage != null) ...[
            const SizedBox(height: 14),

            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: (bucket.progressPercentage! / 100).clamp(0.0, 1.0),
                minHeight: 6,
                backgroundColor: const Color(0xFFE5E7EB),
                color: const Color(0xFFDC2626),
              ),
            ),

            const SizedBox(height: 6),

            Text(
              '${formatPercent(bucket.progressPercentage!)}% of '
              '$currency ${formatMoney(bucket.targetAmount!)}',
              style: const TextStyle(fontSize: 11, color: Color(0xFF697586)),
            ),
          ],
        ],
      ),
    );
  }
}

// --------------------------------------------------
// Grow
// --------------------------------------------------

class _GrowSection extends StatelessWidget {
  final DashboardData data;

  const _GrowSection({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final account = data.grow.accounts.isEmpty
        ? null
        : data.grow.accounts.first;

    return Column(
      children: [
        _DashboardCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _CardLabel(text: 'TOTAL GROWING'),

              const SizedBox(height: 10),

              _MoneyLine(
                currency: data.currency,
                amount: data.grow.investmentBalance,
                amountSize: 35,
              ),

              const SizedBox(height: 12),

              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 7,
                ),
                decoration: BoxDecoration(
                  color: const Color(0xFFE6F6EF),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  '+${data.currency} '
                  '${formatMoney(data.grow.projectedReturn)} '
                  'projected return',
                  style: const TextStyle(
                    color: Color(0xFF008C67),
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 14),

        _DashboardCard(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Investment Balance',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    SizedBox(height: 5),
                    Text(
                      'Held with a licensed partner',
                      style: TextStyle(fontSize: 12, color: Color(0xFF536070)),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Flexible(
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: Alignment.centerRight,
                  child: _MoneyLine(
                    currency: data.currency,
                    amount: data.grow.investmentBalance,
                    amountSize: 18,
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 14),

        _DashboardCard(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Annual Rate',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                  ),

                  SizedBox(height: 5),

                  Text(
                    'Based on your active investment product',
                    style: TextStyle(fontSize: 12, color: Color(0xFF536070)),
                  ),
                ],
              ),

              Text(
                account == null
                    ? '--'
                    : '${formatPercent(account.annualRate)}%',
                style: const TextStyle(
                  fontSize: 21,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
        ),

        if (data.grow.allocated > 0) ...[
          const SizedBox(height: 14),

          _DashboardCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Grow allocation',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    _GrowAmountMetric(
                      label: 'Available',
                      amount: data.grow.available,
                      currency: data.currency,
                    ),
                    _GrowAmountMetric(
                      label: 'Reserved',
                      amount: data.grow.reserved,
                      currency: data.currency,
                    ),
                    _GrowAmountMetric(
                      label: 'Invested',
                      amount: data.grow.invested,
                      currency: data.currency,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                TextButton.icon(
                  onPressed: () => context.go('/grow'),
                  icon: const Icon(Icons.trending_up),
                  label: const Text('Explore investment products'),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

// --------------------------------------------------
// Shared widgets
// --------------------------------------------------

class _GrowAmountMetric extends StatelessWidget {
  final String label;
  final int amount;
  final String currency;

  const _GrowAmountMetric({
    required this.label,
    required this.amount,
    required this.currency,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: Color(0xFF697586)),
          ),
          const SizedBox(height: 4),
          Text(
            '$currency ${formatMoney(amount)}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}

class _DashboardCard extends StatelessWidget {
  final Widget child;

  const _DashboardCard({required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,

      padding: const EdgeInsets.all(20),

      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),

        border: Border.all(color: const Color(0xFFF0F0F0)),

        boxShadow: const [
          BoxShadow(
            color: Color(0x06000000),
            blurRadius: 8,
            offset: Offset(0, 3),
          ),
        ],
      ),

      child: child,
    );
  }
}

class _CardLabel extends StatelessWidget {
  final String text;

  const _CardLabel({required this.text});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w600,
        letterSpacing: 1.0,
        color: Color(0xFF8490A0),
      ),
    );
  }
}

class _MoneyLine extends StatelessWidget {
  final String currency;
  final int amount;
  final double amountSize;

  const _MoneyLine({
    required this.currency,
    required this.amount,
    required this.amountSize,
  });

  @override
  Widget build(BuildContext context) {
    return RichText(
      text: TextSpan(
        children: [
          TextSpan(
            text: '$currency ',
            style: TextStyle(
              fontSize: amountSize * 0.43,
              fontWeight: FontWeight.w600,
              color: const Color(0xFF98A1AD),
            ),
          ),
          TextSpan(
            text: formatMoney(amount),
            style: TextStyle(
              fontSize: amountSize,
              fontWeight: FontWeight.w900,
              letterSpacing: -0.6,
              color: Colors.black,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String label;
  final Color color;

  const _StatusBadge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),

      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.11),
        borderRadius: BorderRadius.circular(7),
      ),

      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.8,
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.cloud_off_rounded,
              size: 48,
              color: Color(0xFFDC2626),
            ),

            const SizedBox(height: 16),

            const Text(
              'Unable to load your dashboard',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFF697586)),
            ),

            const SizedBox(height: 20),

            ElevatedButton(onPressed: onRetry, child: const Text('Try again')),
          ],
        ),
      ),
    );
  }
}
