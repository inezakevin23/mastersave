import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../auth/models/auth_models.dart';
import '../../auth/providers/auth_provider.dart';
import '../models/dashboard_models.dart';
import '../providers/dashboard_provider.dart';

enum DashboardSection { spend, save, grow }

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  DashboardSection section = DashboardSection.spend;

  @override
  Widget build(BuildContext context) {
    final dashboard = ref.watch(dashboardProvider);

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

    final weeklyBudget = spend.weeklyBudget ?? 0;

    final used = spend.usedThisWeek;

    final progress = weeklyBudget == 0
        ? 0.0
        : (used / weeklyBudget).clamp(0.0, 1.0);

    return Column(
      children: [
        _DashboardCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _CardLabel(text: "THIS WEEK'S ALLOWANCE"),

              const SizedBox(height: 12),

              _MoneyLine(
                currency: data.currency,
                amount: weeklyBudget,
                amountSize: 35,
              ),

              const SizedBox(height: 12),

              ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: LinearProgressIndicator(
                  value: progress,
                  minHeight: 6,
                  backgroundColor: const Color(0xFFE5E7EB),
                  color: const Color(0xFFDC2626),
                ),
              ),

              const SizedBox(height: 10),

              Text(
                '${data.currency} '
                '${formatMoney(spend.remainingThisWeek ?? 0)} '
                'left this week',
                style: const TextStyle(fontSize: 13, color: Color(0xFF536070)),
              ),
            ],
          ),
        ),

        const SizedBox(height: 14),

        _DashboardCard(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    spend.currentWeek != null && spend.totalWeeks != null
                        ? 'Week ${spend.currentWeek} '
                              'of ${spend.totalWeeks}'
                        : 'Current week',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                    ),
                  ),

                  const SizedBox(height: 5),

                  const Text(
                    'Used so far this week',
                    style: TextStyle(fontSize: 12, color: Color(0xFF536070)),
                  ),
                ],
              ),

              _MoneyLine(currency: data.currency, amount: used, amountSize: 20),
            ],
          ),
        ),

        const SizedBox(height: 14),

        _DashboardCard(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Weekly Budget',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                  ),

                  const SizedBox(height: 5),

                  Text(
                    _releaseText(spend.nextRelease),
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF536070),
                    ),
                  ),
                ],
              ),

              _MoneyLine(
                currency: data.currency,
                amount: weeklyBudget,
                amountSize: 20,
              ),
            ],
          ),
        ),
      ],
    );
  }

  String _releaseText(DateTime? date) {
    if (date == null) {
      return 'Release schedule unavailable';
    }

    final day = DateFormat('EEEE').format(date);

    final time = DateFormat('h:mm a').format(date);

    return 'Released every $day at $time';
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

              _MoneyLine(
                currency: currency,
                amount: bucket.balance,
                amountSize: 18,
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
              const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Investment Balance',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                  ),

                  SizedBox(height: 5),

                  Text(
                    'Held with a licensed partner',
                    style: TextStyle(fontSize: 12, color: Color(0xFF536070)),
                  ),
                ],
              ),

              _MoneyLine(
                currency: data.currency,
                amount: data.grow.investmentBalance,
                amountSize: 18,
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

        if (data.grow.available > 0) ...[
          const SizedBox(height: 14),

          _DashboardCard(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Available to invest',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),

                    SizedBox(height: 5),

                    Text(
                      'Part of your Grow allocation not yet invested',
                      style: TextStyle(fontSize: 12, color: Color(0xFF536070)),
                    ),
                  ],
                ),

                _MoneyLine(
                  currency: data.currency,
                  amount: data.grow.available,
                  amountSize: 18,
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
